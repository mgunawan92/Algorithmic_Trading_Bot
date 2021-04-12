import numpy as np

class BreakoutAlgorithm(QCAlgorithm):

    # initialize values
    def Initialize(self):
        
        # starting cash balance is $100,000 USD for testing purposes
        self.SetCash(100000)
        
        # set start and end dates for backtesting
        self.SetStartDate(2017,9,1)
        self.SetEndDate(2020,9,1)
        
        # add asset to algorithm using .AddEquity. First parameter is S&P500 equity to add, second parameter is Daily resolution of data
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        # initialize number of days we will look back to determine breakout point in strategy. This will be changed dynamically based on changes in volatility
        self.lookback = 20
        
        # constraints so lookback length does not get too big or too small
        # 30 days for upper limit, 10 days for lower limit
        self.ceiling, self.floor = 30, 10
        
        # how close first stop loss is to security price. initial value of 0.98 will allow for 2 percent loss before it gets triggered
        self.initialStopRisk = 0.98
        
        # how close trailing stop will follow asset's price. initial value of 0.9 will trail for 10%
        self.trailingStopRisk = 0.9
        
        # first parameter specifies which days method is called, second parameter specifies the time method is called (20 minutes after market open below), third specifies which method is called
        self.Schedule.On(self.DateRules.EveryDay(self.symbol), \
                        self.TimeRules.AfterMarketOpen(self.symbol, 20), \
                        Action(self.EveryMarketOpen))
        
    # method called every time algorithm receives new data. method will then decide what action to take with data
    def OnData(self, data):
        # first argument is name of chart to create, second is name of plot, last is data of plot
        self.Plot("Data Chart", self.symbol, self.Securities[self.symbol].Close)
        
    def EveryMarketOpen(self):
        
        # History method returns close, high, low and open price over the past 31 days, although we want only the close
        close = self.History(self.symbol, 31, Resolution.Daily)["close"]
        
        # to calculate volatility, we take standard deviation of the closing price over the past 30 days for the current day
        todayvol = np.std(close[1:31])
        
        # calculate volatility through standard deviation of the closing price over past 30 days for day before
        yesterdayvol = np.std(close[0:30])
        
        # calculate change between volatility of two days
        deltavol = (todayvol - yesterdayvol) / todayvol
        
        # multiply current lookback length by (change in delta) + 1; ensures that lookback length increases when volatility increases, and vice-versa
        self.lookback = round(self.lookback * (1 + deltavol))
        
        # check if lookback length is within previously defined upper and lower limits. If it is not, ensure that it is, otherwise do nothing
        if self.lookback > self.ceiling:
            self.lookback = self.ceiling
        elif self.lookback < self.floor:
            self.lookback = self.floor
        
        # check if breakout is happening. Once again, history returns, in this case, the high price over the period in the lookback length
        self.high = self.History(self.symbol, self.lookback, Resolution.Daily)['high']
        
        # prior to securing any position, verify two things
        
        # 1) that pre-existing investment does not exist
        # 2) verify if last closing price is higher that highest high (self.high variable); last variable is left out so as to not compare yesterday's high to yesterday's close
        # if both conditions are met, purchase SPY at market price using SetHoldings
        if not self.Securities[self.symbol].Invested and self.Securities[self.symbol].Close >= max(self.high[:-1]):
            
            # first parameter is SPY, second is percentage of portfolio that should be allocated to purchase (1 for 100% for demonstration)
            self.SetHoldings(self.symbol, 1)
            
            self.breakoutlvl = max(self.high[:-1])
            self.highestPrice = self.breakoutlvl
            
        # implement trailing stop loss, which is only relevant if there is already a pre-existing open position
        if self.Securities[self.symbol].Invested:
            
            # verify there are no open orders; below GetOpenOrders function will return a collection of orders for security
            if not self.Transactions.GetOpenOrders(self.symbol):
                # send stoploss order; 1st argument is the security, second is the number of shares, third is stoploss price
                # self.Portfolio[].Quantity will return current number of shares owned, minus indicates sell-order
                # stoploss price is calculated by multiplying breakout level by initialized stop risk of 0.98, giving risk of 2%
                self.stopMarketTicket = self.StopMarketOrder(self.symbol, -self.Portfolio[self.symbol].Quantity, self.initialStopRisk * self.breakoutlvl)
            
            # increase stoploss everytime security makes new highs. if no new highs are attained, stoploss remains unchanged
            # conditions mets only if trading stop loss is not below initial stop loss price
            if self.Securities[self.symbol].Close > self.highestPrice and self.initialStopRisk * self.breakoutlvl < self.Securities[self.symbol].Close * self.trailingStopRisk:
                
                # if conditions are met, set highest price to latest closing price
                self.highestPrice = self.Securities[self.symbol].Close
                
                # create UpdateOrderFields() object to update order price of stop loss so that it rises together with securities price
                updateFields = UpdateOrderFields()
                
                # new price is calculated by multiplying trailing stop risk, initialized to 0.9, by latest closing price
                updateFields.StopPrice = self.Securities[self.symbol].Close * self.trailingStopRisk
                
                # update existing stoploss order
                self.stopMarketTicket.Update(updateFields)
                
                # print new stop price to console so that nee order price can be checked every time it is updated
                self.Debug(updateFields.StopPrice)
                
            # plot stop price of position onto previous data chart; allows for viewing where stoploss is relative to trading price of securities
            self.Plot("Data Chart", "Stop Price", self.stopMarketTicket.Get(OrderField.StopPrice))
