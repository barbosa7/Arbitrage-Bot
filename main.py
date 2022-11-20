import logging
import time
from typing import List, Dict
from optibook import common_types as t
from optibook import ORDER_TYPE_IOC, ORDER_TYPE_LIMIT, SIDE_ASK, SIDE_BID
from optibook.exchange_responses import InsertOrderResponse
from optibook.synchronous_client import Exchange
import random
import json


logging.getLogger('client').setLevel('ERROR')
logger = logging.getLogger(__name__)

class Bot:
    def __init__(self, _e: Exchange):
        self.e = _e
        self.BASKET_ID = 'C2_GREEN_ENERGY_ETF'
        self.STOCK_IDS = ['C2_SOLAR_CO', 'C2_WIND_LTD']
        self.trade_history = {
            self.BASKET_ID: None,
            self.STOCK_IDS[0]: None,
            self.STOCK_IDS[1]: None,
        }
        self.cycle_count = 0
        self.bestask_green = 10000000
        self.bestbid_green = -10000000
        self.bestask_fossil = 10000000
        self.bestbid_fossil = -10000000
        self.bestask_greenA = 100000
        self.bestbid_greenA = -10000000
        self.bestask_fossilA = 10000000
        self.bestbid_fossilA = -10000000
        self.bestask_greenB = 100000
        self.bestbid_greenB = -10000000
        self.bestask_fossilB = 10000000
        self.bestbid_fossilB = -100000
        self.increment = 0.1
    
    def is_over_order_limit(self, instrument_id, volume_of_next_order):
        current_orders_volume = 0
        for order in self.e.get_outstanding_orders(instrument_id).values():
            if (order.instrument_id == instrument_id):
                current_orders_volume += order.volume
        return volume_of_next_order + current_orders_volume >= 800 

    def safe_insert_order(self, instrument_id: str, *, price: float, volume: int, side: str, order_type: str = 'limit'):
        if (not self.is_over_order_limit(instrument_id, volume)):
            self.e.insert_order(instrument_id=instrument_id, price=price, volume=volume, side=side, order_type=order_type)

    def set_green(self):
        basket = 'C2_GREEN_ENERGY_ETF'
        stocks = ['C2_SOLAR_CO', 'C2_WIND_LTD']
        return (basket, stocks)


    def set_fossil(self):
        basket = 'C1_FOSSIL_FUEL_ETF'
        stocks = ['C1_GAS_INC', 'C1_OIL_CORP']
        return (basket, stocks)

    def get_trade_history(self, instrument_id: str):
        if (not self.trade_history[instrument_id]):
            self.trade_history[instrument_id] = self.e.get_trade_tick_history(instrument_id)
        return self.trade_history[instrument_id]


    def get_last_trade_price(self, instrument_id: str):
        th = self.get_trade_history(instrument_id)
        if (len(th) == 0):
            return None
        else:
            return th[-1].price


    def print_report(self):
        pnl = self.e.get_pnl()
        positions = self.e.get_positions()
        my_trades = self.e.poll_new_trades(self.BASKET_ID)
        all_market_trades = self.e.poll_new_trade_ticks(self.BASKET_ID)
        logger.info(f'I have done {len(my_trades)} trade(s) in {self.BASKET_ID} since the last report. There have been {len(all_market_trades)} market trade(s) in total in {self.BASKET_ID} since the last report.')
        logger.info(f'My PNL is: {pnl:.2f}')
        logger.info(f'My current positions are: {json.dumps(positions, indent=3)}')

    # edge case where asks is 0 and we need to correct the hedge isn't handled yet


    def is_long_basket(self):
        return len(self.books[self.STOCK_IDS[0]].bids) > 0 and len(self.books[self.STOCK_IDS[1]].bids) > 0 and len(self.books[self.BASKET_ID].asks) > 0 and self.books[self.STOCK_IDS[0]].bids[0].price * 0.5 + self.books[self.STOCK_IDS[1]].bids[0].price * 0.5 > self.books[self.BASKET_ID].asks[0].price


    def is_short_basket(self):
        return len(self.books[self.STOCK_IDS[0]].asks) > 0 and len(self.books[self.STOCK_IDS[1]].asks) > 0 and len(self.books[self.BASKET_ID].bids) > 0 and self.books[self.BASKET_ID].bids[0].price > self.books[self.STOCK_IDS[0]].asks[0].price * 0.5 + self.books[self.STOCK_IDS[1]].asks[0].price * 0.5


    def fix_hedge_short(self):
        if (self.positions[self.STOCK_IDS[0]] > self.positions[self.STOCK_IDS[1]]):
            difference = self.positions[self.STOCK_IDS[0]] - self.positions[self.STOCK_IDS[1]]
            trade_size = min([difference, self.books[self.STOCK_IDS[0]].asks[0].volume])
            if (trade_size > 0):
                self.safe_insert_order(self.STOCK_IDS[1], price=self.books[self.STOCK_IDS[0]].asks[0].price,
                            volume=trade_size, side=SIDE_BID, order_type=ORDER_TYPE_IOC)

            else:
                print("someone was faster")
                print(difference)

        elif (self.positions[self.STOCK_IDS[0]] < self.positions[self.STOCK_IDS[1]]):
            difference = self.positions[self.STOCK_IDS[1]] - self.positions[self.STOCK_IDS[0]]
            trade_size = min([difference, self.books[self.STOCK_IDS[1]].asks[0].volume])
            if (trade_size > 0):
                self.safe_insert_order(
                    self.STOCK_IDS[0], price=self.books[self.STOCK_IDS[1]].asks[0].price, volume=trade_size, side=SIDE_BID, order_type=ORDER_TYPE_IOC)
            else:
                print("someone was faster")
                print(difference)
        else:
            difference = abs(abs(
                self.positions[self.BASKET_ID]) - (abs(self.positions[self.STOCK_IDS[1]]) + abs(self.positions[self.STOCK_IDS[0]])))
            trade_size = min(
                [difference, self.books[self.BASKET_ID].bids[0].volume, 500 - abs(self.positions[self.BASKET_ID])])
            if (trade_size > 1):
                self.safe_insert_order(
                    self.STOCK_IDS[0], price=self.books[self.STOCK_IDS[0]].bids[0].price, volume=trade_size // 2, side=SIDE_BID, order_type=ORDER_TYPE_IOC)
                self.safe_insert_order(
                    self.STOCK_IDS[1], price=self.books[self.STOCK_IDS[1]].bids[0].price, volume=trade_size // 2, side=SIDE_BID, order_type=ORDER_TYPE_IOC)
            else:
                print("someone was faster")
                print(difference)


    def simple_short(self):
        max_position_volume = min([(500 - abs(self.positions[self.BASKET_ID])) // 2,
                                500 - abs(self.positions[self.STOCK_IDS[0]]), 500 - abs(self.positions[self.STOCK_IDS[1]])])
        trade_size = min([max_position_volume, self.books[self.BASKET_ID].bids[0].volume//2,
                        self.books[self.STOCK_IDS[0]].asks[0].volume, self.books[self.STOCK_IDS[1]].asks[0].volume])
        if (trade_size > 0):
            self.safe_insert_order(
                self.BASKET_ID, price=self.books[self.BASKET_ID].bids[0].price, volume=trade_size * 2, side=SIDE_ASK, order_type=ORDER_TYPE_IOC)
            self.safe_insert_order(
                self.STOCK_IDS[0], price=self.books[self.STOCK_IDS[0]].asks[0].price, volume=trade_size, side=SIDE_BID, order_type=ORDER_TYPE_IOC)
            self.safe_insert_order(
                self.STOCK_IDS[1], price=self.books[self.STOCK_IDS[1]].asks[0].price, volume=trade_size, side=SIDE_BID, order_type=ORDER_TYPE_IOC)
        else:
            print("someone was faster")
            print(max_position_volume)


    def short(self):
        if (self.books[self.BASKET_ID].bids and self.books[self.STOCK_IDS[0]].asks and self.books[self.STOCK_IDS[1]].asks):
            if ((abs(self.positions[self.STOCK_IDS[0]]) + abs(self.positions[self.STOCK_IDS[1]]) != abs(self.positions[self.BASKET_ID])) or self.positions[self.STOCK_IDS[1]] != self.positions[self.STOCK_IDS[0]]):
                self.fix_hedge_short()
            self.simple_short()
        else:
            print("one of the books is missing")


    def simple_long(self):
        max_position_volume = min([(500 - abs(self.positions[self.BASKET_ID])) // 2,
                                500 - abs(self.positions[self.STOCK_IDS[0]]), 500 - abs(self.positions[self.STOCK_IDS[1]])])
        trade_size = min([max_position_volume, self.books[self.BASKET_ID].asks[0].volume//2,
                        self.books[self.STOCK_IDS[0]].bids[0].volume, self.books[self.STOCK_IDS[1]].bids[0].volume])
        if (trade_size > 0):
            self.safe_insert_order(
                self.BASKET_ID, price=self.books[self.BASKET_ID].asks[0].price, volume=trade_size * 2, side=SIDE_BID, order_type=ORDER_TYPE_IOC)
            self.safe_insert_order(
                self.STOCK_IDS[0], price=self.books[self.STOCK_IDS[1]].bids[0].price, volume=trade_size, side=SIDE_ASK, order_type=ORDER_TYPE_IOC)
            self.safe_insert_order(
                self.STOCK_IDS[1], price=self.books[self.STOCK_IDS[1]].bids[0].price, volume=trade_size, side=SIDE_ASK, order_type=ORDER_TYPE_IOC)
            print("trades have been made (long)")
        else:
            print("someone was faster")
            print(max_position_volume)


    def fix_hedge_long(self):
        if (self.positions[self.STOCK_IDS[0]] > self.positions[self.STOCK_IDS[1]]):
            difference = self.positions[self.STOCK_IDS[0]] - self.positions[self.STOCK_IDS[1]]
            trade_size = min([difference, self.books[self.STOCK_IDS[0]].bids[0].volume])
            if (trade_size > 0):
                self.safe_insert_order(
                    self.STOCK_IDS[0], price=self.books[self.STOCK_IDS[0]].bids[0].price, volume=trade_size, side=SIDE_ASK, order_type=ORDER_TYPE_IOC)
            else:
                print("someone was faster")
                print(difference)
        elif (self.positions[self.STOCK_IDS[0]] < self.positions[self.STOCK_IDS[1]]):
            difference = self.positions[self.STOCK_IDS[1]] - self.positions[self.STOCK_IDS[0]]
            trade_size = min([difference, self.books[self.STOCK_IDS[1]].bids[0].volume])
            if (trade_size > 0):
                self.safe_insert_order(
                    self.STOCK_IDS[1], price=self.books[self.STOCK_IDS[1]].bids[0].price, volume=trade_size, side=SIDE_ASK, order_type=ORDER_TYPE_IOC)
            else:
                print("someone was faster")
                print(difference)
        else:
            difference = abs(abs(
                self.positions[self.BASKET_ID]) - (abs(self.positions[self.STOCK_IDS[1]]) + abs(self.positions[self.STOCK_IDS[0]])))
            trade_size = min(
                [difference, self.books[self.BASKET_ID].asks[0].volume, (500-self.positions[self.BASKET_ID])])
            if (trade_size > 0):
                self.safe_insert_order(
                    self.BASKET_ID, price=self.books[self.BASKET_ID].asks[0].price, volume=trade_size, side=SIDE_BID, order_type=ORDER_TYPE_IOC)
            else:
                print("someone was faster")
                print(difference)


    def long(self):
        if (self.books[self.BASKET_ID].bids and self.books[self.STOCK_IDS[0]].asks and self.books[self.STOCK_IDS[1]].asks):
            if (abs(self.positions[self.STOCK_IDS[0]]) + abs(self.positions[self.STOCK_IDS[1]]) != abs(self.positions[self.BASKET_ID]) and self.positions[self.STOCK_IDS[1]] != self.positions[self.STOCK_IDS[0]]):
                self.fix_hedge_long()
            self.simple_long()
        else:
            print("one of the books is missing")


    def try_close_all_positions(self):
        self.print_report()
        for instr_id in self.positions.keys():
            book = self.books[instr_id]
            position_volume = self.positions[instr_id]
            if (position_volume > 0):
                for bid in book.bids:
                    trade_volume = min([bid.volume, position_volume])
                    self.safe_insert_order(
                        instr_id, price=bid.price, volume=trade_volume, side=SIDE_ASK, order_type=ORDER_TYPE_IOC)
                    position_volume -= trade_volume
                    if (position_volume == 0):
                        return
            elif (position_volume < 0):
                for ask in book.asks:
                    trade_volume = min([ask.volume, position_volume * -1])
                    self.safe_insert_order(
                        instr_id, price=ask.price, volume=trade_volume, side=SIDE_BID, order_type=ORDER_TYPE_IOC)
                    position_volume += trade_volume
                    if (position_volume == 0):
                        return


    def print_trade_history(self, instr_ids: List[str]):
        for instr_id in instr_ids:
            print(instr_id)
            print(self.e.get_trade_history(instr_id))
            print('')


    def delete_all_orders(self):
        self.e.delete_orders(self.BASKET_ID)
        self.e.delete_orders(self.STOCK_IDS[0])
        self.e.delete_orders(self.STOCK_IDS[1])
        self.cycle_count = 0
        self.bestask_green = 10000000
        self.bestbid_green = -10000000
        self.bestask_fossil = 10000000
        self.bestbid_fossil = -10000000
        self.bestask_greenA = 100000
        self.bestbid_greenA = -10000000
        self.bestask_fossilA = 10000000
        self.bestbid_fossilA = -10000000
        self.bestask_greenB = 100000
        self.bestbid_greenB = -10000000
        self.bestask_fossilB = 10000000
        self.bestbid_fossilB = -100000


    def is_instrument_liquid(self, instrument_id: str):
        return (len(self.books[instrument_id].asks) > 0) and (len(self.books[instrument_id].bids) > 0)


    def market_make(self):
        if (self.is_instrument_liquid(self.BASKET_ID)):
            self.market_make_basket()
        elif (self.get_last_trade_price(self.BASKET_ID) != None):
            self.market_make_illiquid_basket()

        if (self.is_instrument_liquid(self.STOCK_IDS[1])):
            self.market_make_stock(1)
        elif (self.get_last_trade_price(self.STOCK_IDS[1]) != None):
            self.market_make_illiquid_stock(1)
        if (self.is_instrument_liquid(self.STOCK_IDS[0])):
            self.market_make_stock(0)
        elif (self.get_last_trade_price(self.STOCK_IDS[0]) != None):
            self.market_make_illiquid_stock(0)


    def market_make_illiquid_basket(self):
        if (len(self.books[self.BASKET_ID].asks) > 0):
            self.market_make_ask_basket()
        elif (len(self.books[self.BASKET_ID].bids) > 0):
            self.market_make_bid_basket()



    def market_make_illiquid_stock(self,asset):
        if (len(self.books[self.STOCK_IDS[asset]].asks) > 0):
            self.market_make_ask_stock(asset)
        elif (len(self.books[self.STOCK_IDS[asset]].bids) > 0):
            self.market_make_bid_stock(asset)
        else:
            self.market_make_no_orders_stock(asset)



    def market_make_ask_basket(self):
        if (self.BASKET_ID=='C2_GREEN_ENERGY_ETF'):
            self.bestask_green = min([self.books[self.BASKET_ID].asks[0].price-self.increment,self.bestask_green])
            self.bestbid_green = max([self.get_last_trade_price(self.BASKET_ID) - 10,self.bestbid_green])
            no_self_trade = self.bestask_green-self.bestbid_green >=   0.1
        else:
            self.bestask_fossil = min([self.books[self.BASKET_ID].asks[0].price-self.increment,self.bestask_fossil])
            self.bestbid_fossil = max([self.get_last_trade_price(self.BASKET_ID) - 10,self.bestbid_fossil])
            no_self_trade = self.bestask_fossil-self.bestbid_fossil>=0.1

        if no_self_trade:
            #self.increment+=0.1
            net_unhedged = self.positions[self.BASKET_ID] + \
                (self.positions[self.STOCK_IDS[0]] + self.positions[self.STOCK_IDS[0]])
            if 500-self.positions[self.BASKET_ID] > 30:
                self.safe_insert_order(
                    self.BASKET_ID, price=self.get_last_trade_price(self.BASKET_ID) - 10, volume=30, side=SIDE_BID, order_type=ORDER_TYPE_LIMIT)
            if self.positions[self.BASKET_ID]-10-round(abs(net_unhedged/1.5)) < 500 and net_unhedged > -15:
                self.safe_insert_order(
                    self.BASKET_ID, price=self.books[self.BASKET_ID].asks[0].price-self.increment, volume=10+round(abs(net_unhedged/1.5)), side=SIDE_ASK, order_type=ORDER_TYPE_LIMIT)
        #elif (self.increment>0.1):
            #self.increment-=0.1

    def market_make_bid_basket(self):
        if (self.BASKET_ID=='C2_GREEN_ENERGY_ETF'):
            self.bestask_green = min([self.get_last_trade_price(self.BASKET_ID) + 10,self.bestask_green])
            self.bestbid_green = max([self.books[self.BASKET_ID].bids[0].price+self.increment,self.bestbid_green])
            no_self_trade = self.bestask_green-self.bestbid_green >=0.1
        else:
            self.bestask_fossil = min([self.get_last_trade_price(self.BASKET_ID) + 10,self.bestask_fossil])
            self.bestbid_fossil = max([self.books[self.BASKET_ID]-self.increment,self.bestbid_fossil])
            no_self_trade = self.bestask_fossil-self.bestbid_fossil >=0.1
        
        if no_self_trade:
            #self.increment+=0.1
            net_unhedged = self.positions[self.BASKET_ID] + \
                (self.positions[self.STOCK_IDS[0]] + self.positions[self.STOCK_IDS[0]])
            if 500-self.positions[self.BASKET_ID] > 10+round(abs(net_unhedged/1.5)) and net_unhedged < 15:
                self.safe_insert_order(self.BASKET_ID, price=self.books[self.BASKET_ID].bids[0].price+0.05, volume=10+round(
                    abs(net_unhedged/1.5)), side=SIDE_BID, order_type=ORDER_TYPE_LIMIT)
            if self.positions[self.BASKET_ID]-30 < 500:
                self.safe_insert_order(self.BASKET_ID, price=self.get_last_trade_price(self.BASKET_ID) + 10, volume=30,
                            side=SIDE_ASK, order_type=ORDER_TYPE_LIMIT)
        #elif (self.increment>0.1):
            #self.increment -= 0.1

    def market_make_bid_stock(self,asset):
        if self.positions[self.STOCK_IDS[asset]]-50 > -300:
            self.safe_insert_order(self.STOCK_IDS[asset], price=self.get_last_trade_price(self.STOCK_IDS[asset]) + 10, volume=50,
                        side=SIDE_ASK, order_type=ORDER_TYPE_LIMIT)


    def market_make_ask_stock(self,asset):
        if 300-self.positions[self.STOCK_IDS[asset]] > 50:
            self.safe_insert_order(self.STOCK_IDS[asset], price=self.get_last_trade_price(self.STOCK_IDS[asset]) - 10, volume=50,
                        side=SIDE_BID, order_type=ORDER_TYPE_LIMIT)


    def market_make_no_orders_stock(self,asset):
        if 300-self.positions[self.STOCK_IDS[asset]] > 50:
            self.safe_insert_order(self.STOCK_IDS[asset], price=self.get_last_trade_price(self.STOCK_IDS[asset]) - 10, volume=50,
                        side=SIDE_BID, order_type=ORDER_TYPE_LIMIT)
        if self.positions[self.STOCK_IDS[asset]]-50 < 500:
            self.safe_insert_order(self.STOCK_IDS[asset], price=self.get_last_trade_price(self.STOCK_IDS[asset]) + 10, volume=50,
                        side=SIDE_ASK, order_type=ORDER_TYPE_LIMIT)

    # still need to add conditions in order not to break limits

    def market_make_basket(self):
        short_price = self.books[self.BASKET_ID].asks[0].price-self.increment
        long_price = self.books[self.BASKET_ID].bids[0].price+self.increment
        if (self.BASKET_ID=='C2_GREEN_ENERGY_ETF'):
            self.bestask_green = min([short_price,self.bestask_green])
            self.bestbid_green = max([long_price,self.bestbid_green])
            no_self_trade = self.bestask_green-self.bestbid_green >= 0.1
        else:
            self.bestask_fossil = min([short_price,self.bestask_fossil])
            self.bestbid_fossil = max([long_price,self.bestbid_fossil])
            no_self_trade = self.bestask_fossil-self.bestbid_fossil >= 0.1
        print()
        if no_self_trade:
            
            net_unhedged = self.positions[self.BASKET_ID] + \
                (self.positions[self.STOCK_IDS[0]] + self.positions[self.STOCK_IDS[0]])
            if 500-self.positions[self.BASKET_ID] > 24:
                self.safe_insert_order(
                    self.BASKET_ID, price=long_price, volume=24, side=SIDE_BID, order_type=ORDER_TYPE_LIMIT)
            if self.positions[self.BASKET_ID] - 24 > -500:
                self.safe_insert_order(
                    self.BASKET_ID, price=short_price, volume=24, side=SIDE_ASK, order_type=ORDER_TYPE_LIMIT)



    def market_make_stock(self,asset):
        print("preparing to set orders for stock:" + self.STOCK_IDS[asset])
        no_self_trade = True
        short_price = self.books[self.STOCK_IDS[asset]].asks[0].price-self.increment
        long_price = self.books[self.STOCK_IDS[asset]].bids[0].price+self.increment
        if (asset==0):
            if ('SOLAR' in self.STOCK_IDS[asset]):
                self.bestask_greenA = min([short_price,self.bestask_greenA])
                self.bestbid_greenA = max([long_price,self.bestbid_greenA])
                no_self_trade = (self.bestask_greenA-self.bestbid_greenA >= 0.1)
            else:
                self.bestask_fossilA = min([short_price,self.bestask_fossilA])
                self.bestbid_fossilA = max([long_price,self.bestbid_fossilA])
                no_self_trade = (self.bestask_fossilA-self.bestbid_fossilA >= 0.1)
        else:
            if ('WIND' in self.STOCK_IDS[asset]):
                self.bestask_greenB = min([short_price,self.bestask_greenB])
                self.bestbid_greenB = max([long_price,self.bestbid_greenB])
                no_self_trade = (self.bestask_greenB-self.bestbid_greenB >= 0.1)
            else:
                self.bestask_fossilB = min([short_price,self.bestask_fossilB])
                self.bestbid_fossilB = max([long_price,self.bestbid_fossilB])
                no_self_trade = (self.bestask_fossilB-self.bestbid_fossilB >= 0.1)
        if no_self_trade:
            print("going to set orders for stock: " + self.STOCK_IDS[asset])
            if 500-self.positions[self.STOCK_IDS[asset]] > 12:
                self.safe_insert_order(
                    self.STOCK_IDS[asset], price=long_price, volume=12, side=SIDE_BID, order_type=ORDER_TYPE_LIMIT)
            if self.positions[self.STOCK_IDS[asset]]-12 > -500:
                print("short_price: "+ str(short_price))
                print(self.e.get_outstanding_orders(self.STOCK_IDS[asset]))
                self.safe_insert_order(
                    self.STOCK_IDS[asset], price=short_price, volume=12, side=SIDE_ASK, order_type=ORDER_TYPE_LIMIT)


    def arb(self):
        if self.is_long_basket():
            self.long()
        if self.is_short_basket():
            self.short()

    def update_data(self):
        self.positions = self.e.get_positions()
        self.books = {
            self.BASKET_ID: self.e.get_last_price_book(self.BASKET_ID),
            self.STOCK_IDS[0]: self.e.get_last_price_book(self.STOCK_IDS[0]),
            self.STOCK_IDS[1]: self.e.get_last_price_book(self.STOCK_IDS[1]),
        }
        self.trade_history = {
            self.BASKET_ID: None,
            self.STOCK_IDS[0]: None,
            self.STOCK_IDS[1]: None,
        }

    def evaluate_position_risk(self):
        total_size = sum(self.positions.values())
        unhedged_size =  abs(self.positions['C2_GREEN_ENERGY_ETF'] + \
                (self.positions['C2_SOLAR_CO'] + self.positions['C2_WIND_LTD'])) + \
                    abs(self.positions['C1_FOSSIL_FUEL_ETF'] + \
                (self.positions['C1_GAS_INC'] + self.positions['C1_OIL_CORP']))
        return round(total_size/750 + unhedged_size/45)

    def change_market(self):
        if (self.BASKET_ID == 'C2_GREEN_ENERGY_ETF'):
            (self.BASKET_ID, self.STOCK_IDS) = self.set_fossil()
        else:
            (self.BASKET_ID, self.STOCK_IDS) = self.set_green()

    def trade_cycle(self):
        self.change_market()
        self.update_data()
        if (self.cycle_count %  4 == 0):
            self.delete_all_orders()
            risk = self.evaluate_position_risk()
            for x in range(risk):
                self.arb()
                self.update_data()
                time.sleep(0.02)
        else:
            self.market_make()

        self.print_report()
        self.cycle_count += 1

    def run(self):
        sleep_duration_sec = 5 
        while True:
            self.trade_cycle()
            logger.info(
                f'Iteration complete. Sleeping for {sleep_duration_sec} seconds')
            time.sleep(sleep_duration_sec)

if __name__ == '__main__':
    exchange = Exchange()
    exchange.connect()
    Bot(exchange).run()
