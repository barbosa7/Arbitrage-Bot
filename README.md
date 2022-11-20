## Submission file
 is /src/bot.py

## Team
* [Tomás Barbosa](https://github.com/barbosa7)
* [Nader Bennour](https://github.com/naderbennour)
* [Vicente Almeida](https://github.com/almeidavc)

## Inspiration
We had a lot of fun when we were ranked number 1 in the challenge and testing phase. Our goal is to repeat our success in the official testing period and defend our title.

## What it does
Our algorithm is a market-making algorithm that trades the green energy basket and the fossil fuel basket. It continuously quotes 2-sides in the basket's order book, and hedges our trades in the two stocks.

## How we built it
Our algorithm is written in Python and is based on the idea of market-making.

We place orders for asks and bids to try and catch the spread, at the same time we are also trading arbitrage. Our arbitrage bot logically hedges all of his trades, but as a market marker trading in a market with low liquidity we had to take up the less loved side of the trade in non-neutral positions. In this scenario, we take advantage of our arbitrage bot, when it finds an opportunity for a trade it will only open one side of the trade in order to help us achieve market neutrality. This is our goal since we believe our edge is in capturing the spread and not in our ability to predict where the market is going.

We believe our algorithm is resilient to different market conditions, and we are confident it will hold up well when markets get very busy.

## Challenges we ran into
It was a challenge for us to evaluate the correct degree of risk and the correct parameters for our script. We wanted to maximise our profits but also have a consistent strategy which was relatively risk averse. Our way of doing this was by regularly changing the size of our total positions and how much of that was unhedged, as this is how our bot analyses risk. 

We ran into a few challenges when building our algorithm. First, we had to make sure that we properly hedged our trades. We also had to account for the 100 lot limit for the combined "hedged" position.

## Accomplishments that we're proud of
We are proud of our algorithm's performance and profitability. We are also proud of our ability to properly hedge our trades and keep our position within the 100 lot limit.

## What we learned
We learned a lot about market-making and risk management. We also learned how to build an algorithm that is resilient to different market conditions.

## What's next for schmup
We plan on continuing to refine our algorithm and making it even more resilient to different market conditions.
