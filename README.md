Algorithmic Trading Bot (Python/QuantConnect)

Python trading bot built off of standard Breakout Trading strategy:

 - Algorithm observes past highs of given instrument
 - Buy signal will be generated once price exceeds previous high
 - Once security is purchased, stop-loss is implemented to follow price movement conjunctively
 - When price drops by established loss percentage, position will be closed

Algorithm dynamically determines Lookback Length:

  - Lookback Length is determined based on volatility adjustment

    - When volatility for security is high, lookback length reaches further into previous history, and vice-versa when volatility is low
    - Doing so allows for algorithm to automatically adapt to changes in volatility

* Algorithm built using Python, Numpy Library, and QuantConnect Platform
