import yfinance as yf
import numpy as np
import pandas as pd

from datetime import datetime, timedelta
from pathlib import Path

from helperFunctions import *


# --------------------------------------------------------------
# read input data
# --------------------------------------------------------------

portfolio    = fct_markdownTable2dataFrame("pfioParam.md")
transactions = fct_markdownTable2dataFrame("pfioTransactionInput.md")

# --------------------------------------------------------------
# calculate invest budget
# --------------------------------------------------------------

print("Info ivst budget: %.2f" % np.sum(transactions.loc[:, "Pos"].astype(float)))

# --------------------------------------------------------------
# cross validating wkn numbers of portfolio and transaction list
# --------------------------------------------------------------

wknPortfolio    = [wkn for wkn in portfolio.loc[:, "WKN"].unique() if len(wkn) ==6]
wknTransactions = [wkn for wkn in transactions.loc[:, "WKN"].unique() if len(wkn) ==6]

errorFlag = False

for wkn in wknTransactions:
  if wkn not in wknPortfolio:
    print("fehler: wkn %s findet sich nicht in den portfolio parametern." % wkn)
    errorFlag = True

for wkn in wknPortfolio:
  if wkn not in wknTransactions:
    print("warnung: wkn %s findet sich keiner transaktion." % wkn)
    errorFlag = True

if not errorFlag:
  print("info wkn kreuzvalidierung okay!")

# --------------------------------------------------------------
# add amount of share to portfolio
# --------------------------------------------------------------

portfolio["N"] = "0.000000"

for it, title in portfolio.iterrows():
  wkn       = title.loc["WKN"]
  taList    = transactions[transactions["WKN"] == wkn] # transactions of title
  amountEks = [elem for elem in taList.loc[taList["Typ"] == "EK", "N"]]
  amountEks = np.sum([int(elem.replace(".","")) for elem in amountEks])
  amountVks = [elem for elem in taList.loc[taList["Typ"] == "VK", "N"]]
  amountVks = np.sum([int(elem.replace(".","")) for elem in amountVks])
  amountSum = amountEks - amountVks
  # perspectively add amount of shares validation for DD transactions
  # perspectively stocksplit mode like SP 15.000000 for 10 >> 150 shares
  amount = "%6d.%06d" % (amountSum // 1e6, amountSum % 1e6)
  portfolio.loc[it, "N"] = amount
  #print("%s: %s ..... %s" % (wkn, portfolio.loc[it, "N"], title["Name"]))

# --------------------------------------------------------------
# load price, load dividend and calculate value of each title
# --------------------------------------------------------------

portfolio["Kurs"]  = "0.0000"
portfolio["Wert"]  = "0.00"
portfolio["RelDD"] = "0.00"

for it, title in portfolio.iterrows():
  symbol    = title.loc["Symbol"]
  stock     = yf.Ticker(symbol)
  fastInfo  = stock.fast_info
  dividends = stock.dividends
  price     = fastInfo.get("lastPrice")
  portfolio.loc[it, "Kurs"] = "%10.4f" % price

  if not dividends.empty:
    lastDividend               = dividends.iloc[-1]
    lastDividendDate           = dividends.index[-1].strftime("%y%m%d")
    relDividend                = lastDividend / price * 100
    portfolio.loc[it, "RelDD"] = "%5.2f %% @ %s" % (relDividend, lastDividendDate)
  else:
    portfolio.loc[it, "RelDD"] = "keine..Dividende"

  value = float(portfolio.loc[it, "N"]) * float(portfolio.loc[it, "Kurs"])
  portfolio.loc[it, "Wert"] = "%8.2f" % value

  print("%s: %s x %s = %s // %s ..... %s" % (wkn,
    portfolio.loc[it, "N"],
    portfolio.loc[it, "Kurs"],
    portfolio.loc[it, "Wert"],
    portfolio.loc[it, "RelDD"],
  title["Name"]))

# --------------------------------------------------------------
# output extended portfolio data as markdown table
# --------------------------------------------------------------

outStrPortfolioMdTable = fct_dataFrame2markdownTable(portfolio, alignment=["l", "l", "l", "l", "l", "l", "l"])

with open("portfolioOutput.md", "w") as fid:
  fid.write(outStrPortfolioMdTable)

# portfolio, transactions = fct_linkTransactions(portfolio, transactions)

# transactions = fct_cummulateCnts(transactions)
# transactions = fct_cummulateSums(transactions)
# transactions = fct_cummulateAmountOfShares(transactions)
# transactions = fct_targetValueCalculation(transactions, portfolio)
# transactions = fct_finalTargetValueCalculation(transactions, portfolio)
# transactions = fct_setEkFlag(transactions, portfolio)
# transactions = fct_calculatedNkThres(transactions, portfolio)
# transactions = fct_calculatedVkThres(transactions, portfolio)

# # sort transactions by title
# fct_exportTransactionsOfEachTitle(transactions, portfolio, PATH_OUTPUT_DATA + "transaktionenJedesTitelNachKuerzel/")

# # process portfolio status
# portfolio = fct_exportPortfolioStatus(transactions, portfolio, outFile="portfolioStatus.txt")
