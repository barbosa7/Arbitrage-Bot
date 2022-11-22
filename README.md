### Introduction

This Bot was made with the purpose of competing in a Hackathon against the bots of other teams in a closed environment (there were also some bots from the event organizers).

this bot was also connected to the events api and using it's calls, i've been asked to remove the api import and change the name of the api functions just so thatin case they repeat this challenge the code won't be found online. That's why you'll see some functions that are called from the exchange that don't seem to exist, they are replacing the original api calls but I think their names represent accurately what the functions do.

The stocks and ETFs were ficticious, meaning there were no fundamentals to trade on, but there were a limited number of participants in the market (about 50 teams) so the market was a bit inefficient. The best 2 ways to make money were to do Arbitrage and to be a Market Maker, so I used a hybrid strategy between both.

It's also important to mention that, since there were no fundamentals, there was no reason to trade directionally and it would increase the risk, I tried to stay market neutral to try not to be dependent on market fluctuations in either direction.

The market I was trading on included 6 Assets, 4 Stocks and 2 ETFs, each of the ETFs represented 2 of the 4 Stocks so the value of ETF 1 should be ETF 1 = Stock A * 0.5 + Stock B * 0.5 and ETF 2 = Stock C * 0.5 + Stock D * 0.5. since both of the ETF/stock relationships are the same and so were the strategies I used on them, I will just refer to bothe the ETFs as ETF and Stock A/C will be stock A just like Stock B/D will be Stock B for simplification purposes.

### Arbitrage Strategy

Since ETF = Stock A * 0.5 + Stock B * 0.5 the price of the ETF should be the average of the prices of the 2 stocks. But the market was illiquid and you couldn't actually redeem Stock A and Stock B from the ETF so the equation didn't always hold up for the prices, it did hold up for the value though, meaning there was a good oportunity for arbitrage.

When the bot find this oportunity, he take it, usually by longing the ETF and shorting the stocks in equal size to stay market neutral or vice versa, this is done with imediate or cancel orders. but there is a caveat, if the position is not market neutral be it because the market making strategy put us on a directional position or because in one of the the previous trades part of the trade didn't go through, the bot needs to hedge himself first. The way he does this in that scenario is by only executing part of the trade. Let's say he decides it's time to long stocks and short the ETF, but he sees that we have some unhedged short on the ETF, he will first of all long the stocks in a certain amount to try to hedge the position.

### Market Making Strategy

the market making strategy is a bit more complex, the market making strategy is relatively independent from the asset it is going to be executing in, I'm going to refer to stocks and the ETF as "asset" and the "market" as the market for that specific asset and it's order book. the first thing I do is check the liquidity of the market to act in, this is only relevant because the general liquidity is so low, if you're acting in a liquid market you can just assume that the asset is always liquid. here there a 4 possibilities, stock is liquid if the order book has both bids and asks and illiquid if it has neither, it can also be half liquid, in this case it either has only asks and no bids or vice versa.

If the Market is liquid the bot looks at the top ask and the top bid and makes a new ask and a new bid that are more competitive by 0.1 (in this exchange the values you traded at were discrete meaning that an increment of less than 0.1 was irrelevant, if you try to implement something like this you might have to adjust this value). This will be limit orders and they will only be done under the condition that even with the increment the ask is still higher than the bid, the point is that due to volatility even if it's really small, chances are both of the orders will be filled since they are so closed together and then the bot gains money from the spread. the bot keeps doing for a while, even if the top orders ar his, because it's possible that the spread is just to big and people don't want to trade, so the bot tightens the spread a bit to entice people to trade and pay him the spread.

Altenatively, the market can also be illiquid, in this case the market could be illiquid for the asks or for the bids or both, I'll talk about what would happen if the bid side was illiquid, in the other cases the same thing would happen but for the other side. In theory, if there were no bids, you could place a bid for 0.1 and hope that someone wouldn't look at the price and would just buy, maybe because they are getting their positions liquidated or maybe because they are just market buying, either way you could get your order filled for an insanely low price and make a lot of money. Unfortunately in this case I couldn't do this, since the exchange didn't allow orders that had a price that was very different from the price of the last trade, so what I did was I looked at the price of the last trade and tried to buy it considerably cheaper than that (-10), but not so cheap that it would trigger tha flags for the exchange.

### Making it hybrid

this are our 2 individual strategies, but they still need to be combined somehow. We started by running the 2 strategies alternately, but the main problem is that everytime we run the arbitrage strategy we need to close the market making limit orders before to prevent us from trading against ourselves which makes our marekt making algorithm considerably slower. The solution I found was to run both the algorithm a certain amount of times in a row and then changing the algorithm. This also has the advantage that we arbitrage better, everytime we run arbitrage we only look at the best best bid (I will talk about the bids side but refering to both sides again), but it's possible that even with the second best bid we would have a profitable arbitrage opportunity. By runnig it multiple times, the first time will take the first best bid out of the order book and the second time will take the second and so on. 

It's important to understand that market making is the "risky" function while arbitrage is relatively safe. Maket making is also a lot more likely to create unhedged positions since the our limit orders might simply not get filled. so it's a good idea to look at the strategies in the following way:
>Market making makes solid money but is a bit reckless, it's doesn't really care about staying market neutral, although the idea is that in the long run it would because the unfilled orders from both sides would even themselves out. On the other side, the arbitrage strategy prioritizes fixing the hedge **without paying a premium**.

With this understanding of the functions, I decided to build a function to determine the risk of our open positions. This function was relatively unsophisticated and could be improved, it determines the size of our total position and how much of it is unhedged. With this risk calculation we determine how often we want to run the arbitrage strategy. Bascally the idea is to determine the amount of times we run the arbitrage per market making cycle is determined dynamically depending on how much risk we're exposed to, so that we prioritize lowering our risk more when we have more risk.

### leaving money on the table

There are a few ways in which the bot is currently leaving money on the table, since it was built in a Hackathon and the amount of time was limited. That being said, this are the key things that could be done to improve it:

* **taking full advantage of illiquid markets:** when the market is illiquid is when there are best opportunities. We take the last trade and add/subtract the value by 10 because of the price change limit, but the limit is not 10. The limit of the exchange was being calculated dynamically and I didn't have time to reverse engeneer it but it would make the strategy more profitable.

 
* **improving the risk function:**  like I said, the function is relatively unsophisticated and obviously making it more accurate would be of good use.

* **dynamic parameters:** the parameters I choose for the script were the best I found, that being said a lot of them were only the best in the moment I found them since the market keeps changing. The best way to account for this change would be for this parameters to be calculated on a dynamic way by reading the market. There also parameters that should be based on the current risk like order size, I tried to implement this at the end but couldn't figure out a way to make it profitable in time and ended up deleting it. 

### parameters

there are a few numbers in the function that could be changed, this is why they were chosen like this:

* **max position size: 500** - (decided by the event organizers)
* **max position unhedged size: 50** - (decided by the event organizers)
* **max order volume open: 800** - (decided by the event organizers)
* **market making (liquid) order size: 12** (24 for ETFS) - small enough that we can make a lot of them without reaching the limits, but big enough that it is relevant
* **market making (illiquid) order size: 50** - we don't have a lot of this opportunities so this should be as greedy possible. Since this is unhedged iy would be a bit risky making it more than 50 though.
* **amount of times to run the market making strategy before arbitrage: 3** - :point_down:
* **sleep time between cycles : 5 seconds** - we tried a lot of different things and the combination between 3 calls and 5 seconds sleep was the best we found, this allows the orders enough time to be filled, making the 3 bigger would mean that it would happen more often that we have already reached the position size or roder limits and would just be wasting time while making the time smaller would increase the chance that our orders don't get filled.

