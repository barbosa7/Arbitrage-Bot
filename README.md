### Introduction

This Bot was made with the purpose of competing in a Hackathon against the bots of other teams in a closed environment (there were also some bots from the event organizers).

The stocks and ETFs were ficticious, meaning there were no fundamentals to trade on, but there were a limited number of participants in the market (about 50 teams) so the market was a bit inefficient. The best 2 ways to make money were to do Arbitrage and to be a Market Maker, so we used a hybrid strategy between both.

It's also important to mention that, since there were no fundamentals, there was no reason to trade directionally and it would increase our risk, we tried to stay market neutral to try not to be dependent on market fluctuations in either direction.

The market we were trading on included 6 Assets, 4 Stocks and 2 ETFs, each of the ETFs represented 2 of the 4 Stocks so the value of ETF 1 should be ETF 1 = Stock A * 0.5 + Stock B * 0.5 and ETF 2 = Stock C * 0.5 + Stock D * 0.5. since both of the ETF/stock relationships are the same and so were the strateggies we used on them, we will just refer to bothe the ETFs as ETF and Stock A/C will be stock A just like Stock B/D will be Stock B for simplification purposes.

### Arbitrage Strategy

Since ETF = Stock A * 0.5 + Stock B * 0.5 the price of the ETF should be the average of the prices of the 2 stocks. But the market was illiquid and you couldn't actually redeem Stock A and Stock B from the ETF so the equation didn't always hold up for the prices, it did hold up for the value though, meaning there was a good oportunity for arbitrage.

