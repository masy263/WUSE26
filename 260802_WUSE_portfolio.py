import yfinance as yf
import pandas as pd

from datetime import datetime, timedelta
from pathlib import Path


# --------------------------------------------------------------
# PARAMETER
# --------------------------------------------------------------

WHILE_INTERUPT = 10000

PATH_OUTPUT_DATA = "data/"

INITIAL_TARGET_VALUE = 300
YAERLY_TARGET_VALUE_INCREASE = 0.06

TYP_A_THRESHOLD_SELL = 0.5
TYP_B_THRESHOLD_SELL = 0.25
TYP_C_THRESHOLD_SELL = 0.20
TYP_D_THRESHOLD_SELL = 0.25

TYP_A_THRESHOLD_BUY = -0.16
TYP_B_THRESHOLD_BUY = -0.12
TYP_C_THRESHOLD_BUY = -0.1

MINIMUM_PURCHASE_SUM = 50

TYP_A_SELL_INCREASE = 0.5
TYP_B_SELL_INCREASE = 0
TYP_C_SELL_INCREASE = 0
TYP_D_SELL_INCREASE = 0
TYP_A_BUY_DECREASE  = 0
TYP_B_BUY_DECREASE  = 0
TYP_C_BUY_DECREASE  = 0.5

MAX_NK_TYP_A = 3
MAX_NK_TYP_B = 2
MAX_NK_TYP_C = 1

MAX_AGE_PRICE = timedelta(hours=0, minutes=30)
PRICE_FILE = "priceList.csv"

SHOW_NEAR_NK_TRANSACTION_THRES = 0.05
SHOW_NEAR_VK_TRANSACTION_THRES = -0.05

# --------------------------------------------------------------
# TRANSACTION KEY
# --------------------------------------------------------------

NONE_WKN_DUMMY = "NO_WKN"
NEXT_TRANSACTION = "nextTa"
PREV_TRANSACTION = "prevTa"
AMOUNT_OF_SHARES = "amount"
TARGET_VALUE = "targetValue"
EK_FLAG = "enEk"
NK_VALUE  = "nkValue"
NK_PRICE  = "nkPrice"
NK_AMOUNT = "nkAmount"
VK_VALUE  = "vkValue"
VK_PRICE  = "vkPrice"
VK_AMOUNT = "vkAmount"

EK_CNT = "cntEk"
VK_CNT = "cntVk"
NK_CNT = "cntNk" # Nachkauf
DD_CNT = "cntDd"
GB_CNT = "cntGb"
TA_CNT = "cntTransaction"

cntList = [EK_CNT, VK_CNT, NK_CNT, DD_CNT, GB_CNT, TA_CNT]

EK_SUM = "sumEk"
VK_SUM = "sumVk"
DD_SUM = "sumDd"
GB_SUM = "sumGb"
TA_SUM = "sumTransaction"

sumList = [EK_SUM, VK_SUM, DD_SUM, GB_SUM, TA_SUM]

# --------------------------------------------------------------
# title keys
# --------------------------------------------------------------

INITAL_TRANSACTION = "initTa"
LAST_TRANSACTION   = "lastTa"
TRANSACTION_HISTORY = "histTa"
PRICE = "price"



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_readPfioParameters(fname):
  """
  Reads portfolio parameter data from given input file which includes (currently 260711):
  Name, Kurz (short name, 6 chars), Symbol (ticker symbol), WKN, Branche, Region, Typ (ETF, A, B, C, D)

  Parameters
  ----------
  fname : string
    Parameters input file

  Returns
  -------
  nPortfolio : int
    Number of titles in portfolio
  portfolio : dict
    Dict with subdicts for each title in portfolio
  """

  pfio = dict()

  with open(fname, "r") as fid:
    inpLines = fid.readlines()

  it = 0
  while inpLines[0][0] != "|" and it < WHILE_INTERUPT:
    inpLines = inpLines[1:]
    it += 1

  if it >= WHILE_INTERUPT: print("Warning: Reached WHILE_INTERUPT")

  it = 0
  while inpLines[-1][0] != "|" and it < WHILE_INTERUPT:
    inpLines = inpLines[:-1]
    it += 1

  if it >= WHILE_INTERUPT: print("Warning: Reached WHILE_INTERUPT")

  inpIndx = inpLines[0][1:-2].replace(" ", "").split("|")
  inpData = inpLines[2:]

  for title in inpData:
    args = title[1:-2].replace(" ", "").split("|")

    tmp = dict()

    for jt, indx in enumerate(inpIndx):
      if indx == "WKN":
        wkn = args[jt]
      else:
        tmp[indx] = args[jt]

    pfio[wkn] = tmp

  nPfio = len(inpData)

  return nPfio, pfio



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_readTransactionsFromFile(fname):
  nTransact    = 0
  transactions = dict()
  ivstSum      = 0 # define overall investment sum

  with open(fname, "r") as fid: inpLines = fid.readlines() # read input file

  inpIndx = inpLines[0][1:-2].replace(" ", "").split("|") # read indexes from table header
  inpData = inpLines[2:] # read data lines
  
  for nr, transaction in enumerate(inpData): # go thorugh each transaction
    args        = transaction[1:-2].replace(" ", "").split("|") # strip data line and split into args
    transaction = dict() # generate temp transaction dict

    for jt, indx in enumerate(inpIndx): transaction[indx] = args[jt]  # copy input data into transaction dict

    if len(transaction["WKN"]) != 6: transaction["WKN"] = NONE_WKN_DUMMY  # mark transactions with no corresponding title

    transactions[nr] = transaction

    ivstSum += int(transaction["Pos"].replace(".", "")) # cummulate overall investment sum

  nTransact = len(inpData)

  print("IVST: %+9.2f" % (ivstSum / 100))

  return nTransact, transactions



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_linkTransactions(portfolio, transactions):

  for nr in transactions:
    transaction = transactions[nr]

    if transaction["WKN"] != NONE_WKN_DUMMY:
      title = portfolio[transaction["WKN"]]

      if INITAL_TRANSACTION not in title.keys():
        title[INITAL_TRANSACTION] = nr
        title[TRANSACTION_HISTORY] = []
      else:
        transaction[PREV_TRANSACTION] = title[LAST_TRANSACTION]
        transactions[title[LAST_TRANSACTION]][NEXT_TRANSACTION] = nr

      title[LAST_TRANSACTION] = nr
      title[TRANSACTION_HISTORY].append(nr)

      portfolio[transaction["WKN"]] = title

    transactions[nr] = transaction

    # print(transaction)

  return portfolio, transactions



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_cummulateCnts(transactions):

  for nr in transactions:
    transaction = transactions[nr]

    if PREV_TRANSACTION in transaction.keys():
      for cnt in cntList: transaction[cnt] = transactions[transaction[PREV_TRANSACTION]][cnt]
      if transaction["Typ"] == "EK": transaction[NK_CNT] += 1
      if transaction["Typ"] == "VK": transaction[NK_CNT]  = 0
    else:
      for cnt in cntList: transaction[cnt] = 0
    
    if transaction["Typ"] == "EK": transaction[EK_CNT] += 1
    if transaction["Typ"] == "VK": transaction[VK_CNT] += 1
    if transaction["Typ"] == "DD": transaction[DD_CNT] += 1
    if transaction["Typ"] == "GB": transaction[GB_CNT] += 1

    transaction[TA_CNT] +=1

    transactions[nr] = transaction

    #print(transaction)
    
  return transactions



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_cummulateSums(transactions):

  for nr in transactions:
    transaction = transactions[nr]

    if PREV_TRANSACTION in transaction.keys():
      for sum in sumList: transaction[sum] = transactions[transaction[PREV_TRANSACTION]][sum]
    else:
      for sum in sumList: transaction[sum] = 0

    sumAsInt = int(transaction["Pos"].replace(".", ""))
    
    if transaction["Typ"] == "EK": transaction[EK_SUM] += sumAsInt
    if transaction["Typ"] == "VK": transaction[VK_SUM] += sumAsInt
    if transaction["Typ"] == "DD": transaction[DD_SUM] += sumAsInt
    if transaction["Typ"] == "GB": transaction[GB_SUM] += sumAsInt

    transaction[TA_SUM] += sumAsInt

    transactions[nr] = transaction

    #print(transaction)
    
  return transactions



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_cummulateAmountOfShares(transactions):

  for nr in transactions:
    transaction = transactions[nr]

    if PREV_TRANSACTION in transaction.keys():
      transaction[AMOUNT_OF_SHARES] = transactions[transaction[PREV_TRANSACTION]][AMOUNT_OF_SHARES]
    else:
      transaction[AMOUNT_OF_SHARES] = 0

    if transaction["Typ"] == "EK": transaction[AMOUNT_OF_SHARES] += int(transaction["N"].replace(".", ""))
    if transaction["Typ"] == "VK": transaction[AMOUNT_OF_SHARES] -= int(transaction["N"].replace(".", ""))

    transactions[nr] = transaction

    # amount mismtach check
    # if transaction["Typ"] == "DD":
    #   amountCheck = (transaction[AMOUNT_OF_SHARES] == int(transaction["N"].replace(".", "")))

    #   if not amountCheck:
    #     print("Amount missmatch: [%s]: %d :: %d" % (transaction["WKN"], transaction[AMOUNT_OF_SHARES], int(transaction["N"].replace(".", ""))))

    #print(transaction)
    
  return transactions



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_targetValueCalculation(transactions, portfolio):

  for nr in transactions:
    transaction = transactions[nr]

    if PREV_TRANSACTION in transaction.keys():
      targetValueOld = transactions[transaction[PREV_TRANSACTION]][TARGET_VALUE]
      targetValueNew = targetValueOld
      title          = portfolio[transaction["WKN"]]

      currTransactionDate = int(transaction["Datum"])
      lastTransactionDate = int(transactions[transaction[PREV_TRANSACTION]]["Datum"])
      diffTransactionDate = currTransactionDate - lastTransactionDate

      if diffTransactionDate < 0: print(
        "FEHLER [%s] Datum der aktuellen Transaktion liegt vor der vorherigen Transaktion." % transaction["WKN"]
        )

      currTransactionDate = (currTransactionDate - (currTransactionDate % 10000)) // 10000
      lastTransactionDate = (lastTransactionDate - (lastTransactionDate % 10000)) // 10000
      diffTransactionDate = currTransactionDate - lastTransactionDate

      if diffTransactionDate > 0: targetValueNew = targetValueOld * (1 + YAERLY_TARGET_VALUE_INCREASE)**diffTransactionDate

      nkDecrease, vkIncrease = 0, 0

      if title["Typ"] == "A": nkDecrease, vkIncrease = TYP_A_BUY_DECREASE * TYP_A_THRESHOLD_BUY, TYP_A_SELL_INCREASE * TYP_A_THRESHOLD_SELL
      if title["Typ"] == "B": nkDecrease, vkIncrease = TYP_B_BUY_DECREASE * TYP_B_THRESHOLD_BUY, TYP_B_SELL_INCREASE * TYP_B_THRESHOLD_SELL
      if title["Typ"] == "C": nkDecrease, vkIncrease = TYP_C_BUY_DECREASE * TYP_C_THRESHOLD_BUY, TYP_C_SELL_INCREASE * TYP_C_THRESHOLD_SELL

      if transaction["Typ"] == "VK": targetValueNew * (1 + vkIncrease)
      if transaction["Typ"] == "EK": targetValueNew * (1 + nkDecrease)

      title[TARGET_VALUE]       = targetValueNew
      transaction[TARGET_VALUE] = targetValueNew
    else:
      transaction[TARGET_VALUE] = INITIAL_TARGET_VALUE

    transactions[nr] = transaction

    # print("%s [%s] %10.2f" % (transaction["Datum"], transaction["WKN"], transaction[TARGET_VALUE]))

  return transactions



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_finalTargetValueCalculation(transactions, portfolio):

  for wkn in portfolio:
    title           = portfolio[wkn]
    lastTransaction = transactions[title[LAST_TRANSACTION]]
    transactionYear = int(lastTransaction["Datum"][0:2])
    currentYear     = int(datetime.now().strftime("%y"))
    diffYear        = currentYear - transactionYear

    if diffYear > 0:
      oldTarget                     = lastTransaction[TARGET_VALUE]
      newTarget                     = oldTarget * (1 + YAERLY_TARGET_VALUE_INCREASE)**(diffYear)
      lastTransaction[TARGET_VALUE] = newTarget

      transactions[title[LAST_TRANSACTION]] = lastTransaction

      # print("updated [%s] from %.2f to %.2f" % (wkn, oldTarget, newTarget))

  return transactions



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_setEkFlag(transactions, portfolio):

  for nr in transactions:
    transaction          = transactions[nr]
    wkn                  = transaction["WKN"]
    transaction[EK_FLAG] = False

    if wkn != NONE_WKN_DUMMY:
      type                 = portfolio[transaction["WKN"]]["Typ"]

      if (type == "A") and (transaction[NK_CNT] < MAX_NK_TYP_A): transaction[EK_FLAG] = True
      if (type == "B") and (transaction[NK_CNT] < MAX_NK_TYP_B): transaction[EK_FLAG] = True
      if (type == "C") and (transaction[NK_CNT] < MAX_NK_TYP_C): transaction[EK_FLAG] = True

    transactions[nr] = transaction

    # print("%s [%s] %s %s" % (transaction["Datum"], wkn, type, transaction[EK_FLAG]))

  return transactions



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_calculatedNkThres(transactions, portfolio):

  for nr in transactions:
    transaction          = transactions[nr]
    wkn                  = transaction["WKN"]

    if wkn != NONE_WKN_DUMMY:
      type                 = portfolio[transaction["WKN"]]["Typ"]
      keepGoing            = True

      if (type == "A"):
        nkThres   = TYP_A_THRESHOLD_BUY
        valueDrop = TYP_A_BUY_DECREASE

      if (type == "B"):
        nkThres   = TYP_B_THRESHOLD_BUY
        valueDrop = TYP_B_BUY_DECREASE

      if (type == "C"):
        nkThres   = TYP_C_THRESHOLD_BUY
        valueDrop = TYP_C_BUY_DECREASE

      if (type == "D") or (type == "ETF"): keepGoing = False
# output

      if keepGoing:
        targetValue = transaction[TARGET_VALUE]
        buyInPos    = targetValue * nkThres * (valueDrop - 1) # equals: upcomingTargetValue - targetValue * (1 + nkThres)

        if buyInPos < MINIMUM_PURCHASE_SUM: buyInPos = MINIMUM_PURCHASE_SUM

        buyInValue  = targetValue - buyInPos / (1 - valueDrop)

        transaction[NK_VALUE]  = buyInValue
        transaction[NK_PRICE]  = buyInValue / transaction[AMOUNT_OF_SHARES] * 1e6
        transaction[NK_AMOUNT] = buyInPos / transaction[NK_PRICE]

        # print("%s [%s] %s %6.2f %6.2f %6.2f" % (transaction["Datum"], portfolio[transaction["WKN"]]["Kurz"], type, transaction[NK_VALUE], transaction[NK_PRICE], transaction[NK_AMOUNT]))

    transactions[nr] = transaction


  return transactions



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_calculatedVkThres(transactions, portfolio):

  for nr in transactions:
    transaction = transactions[nr]
    wkn         = transaction["WKN"]

    if wkn != NONE_WKN_DUMMY:
      type                 = portfolio[transaction["WKN"]]["Typ"]
      keepGoing            = True

      if (type == "A"):
        vkThres    = TYP_A_THRESHOLD_SELL
        valueRaise = TYP_A_SELL_INCREASE

      if (type == "B"):
        vkThres    = TYP_B_THRESHOLD_SELL
        valueRaise = TYP_B_SELL_INCREASE

      if (type == "C"):
        vkThres    = TYP_C_THRESHOLD_SELL
        valueRaise = TYP_C_SELL_INCREASE

      if (type == "D"):
        vkThres    = TYP_D_THRESHOLD_SELL
        valueRaise = TYP_D_SELL_INCREASE

      if (type == "ETF"): keepGoing = False
      if not transaction[AMOUNT_OF_SHARES] > 0: keepGoing = False

      if keepGoing:
        targetValue    = transaction[TARGET_VALUE]
        targetValueNew = targetValue * (1 + valueRaise * vkThres)
        sellValue      = targetValue * (1 + vkThres)
        sellPrice      = sellValue / transaction[AMOUNT_OF_SHARES] * 1e6
        sellPos        = sellValue - targetValueNew
        sellAmount     = (((sellPos / sellPrice) * 64) // 1) / 64

        transaction[VK_VALUE]  = sellValue
        transaction[VK_PRICE]  = sellPrice
        transaction[VK_AMOUNT] = sellAmount

        # print("%s [%s] %s %6.2f %6.2f %12.6f" % (transaction["Datum"], portfolio[transaction["WKN"]]["Kurz"], type, transaction[VK_VALUE], transaction[VK_PRICE], transaction[VK_AMOUNT]))

    transactions[nr] = transaction


  return transactions



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_printTransaction(transaction, sum):
  amntTa =  transaction["N"].replace(".","")
  if amntTa == "": amntTa = 0
  else: amntTa = int(amntTa)

  price =  transaction["Kurs"].replace(".","")
  if price == "": price = 0
  else: price = int(price)

  pos    =  int(transaction["Pos"].replace(".",""))
  sum   += pos

  outStr  = "%s  "     % transaction["Datum"]
  outStr += "%s   "    % transaction["Typ"]
  outStr += "%11.6f  " % (amntTa * 1e-6)
  outStr += "%11.6f  " % (transaction[AMOUNT_OF_SHARES] * 1e-6)
  outStr += "%9.4f  "  % (price * 1e-4)
  outStr += "%s  "     % transaction["WRG"]
  outStr += "%+9.2f  " % (pos * 1e-2)
  outStr += "%+9.2f  " % (sum * 1e-2)

  return sum, outStr



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_printTransactions(transactions):
  cummulatedSum = 0
  outStr        = "Datum   Typ  N-TA         N-SUM        Kurs       WRG  Pos        Sum\n"

  for nr in transactions:
    tranaction             = transactions[nr]
    cummulatedSum, tmpStr  = fct_printTransaction(tranaction, cummulatedSum)
    outStr                += tmpStr + "\n"


  return outStr



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_exportTransactionsOfEachTitle(transactions, portfolio, outFilePrefix=""):

  if outFilePrefix != "":
   directory = Path(outFilePrefix)
   directory.mkdir(parents=True, exist_ok=True)
  
  for wkn in portfolio:
    title           = portfolio[wkn]
    history         = title[TRANSACTION_HISTORY]
    tempTansactions = dict()

    for nr in history:
      tempTansactions[nr] = transactions[nr]

    with open(outFilePrefix + title["Kurz"] + ".csv", "w") as fid:
      fid.write(fct_printTransactions(tempTansactions))



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_getCurrentPrice(ticker):
    stock = yf.Ticker(ticker)

    info  = stock.fast_info
    price = info.get("lastPrice")

    if price is None:
        hist = stock.history(period="1d", interval="1m")
        if hist.empty:
            raise ValueError(f"Kein Kurs für '{ticker}' verfügbar.")
        price = hist["Close"].iloc[-1]

    return float(price)



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_getCachedPrice(symbol, priceCache, now, maxAge=MAX_AGE_PRICE):
    """
    Liefert den aktuellen Kurs.

    Existiert ein Cache-Eintrag und ist dieser jünger als
    'maxAge', wird der gespeicherte Preis verwendet.
    Andernfalls wird Yahoo Finance abgefragt und der Cache
    aktualisiert.
    """

    row = priceCache[priceCache.symbol == symbol]

    if not row.empty:
      timeStamp = datetime.fromisoformat(row.iloc[0]["timeStamp"])

      if now - timeStamp <= maxAge:
        return int(float(row.iloc[0]["price"]) * 1e4)

    # Cache fehlt oder ist veraltet.
    price     = fct_getCurrentPrice(symbol)
    timeStamp = now.isoformat(timespec="seconds")

    if row.empty:
      priceCache.loc[len(priceCache)] = {"symbol": symbol, "timeStamp": timeStamp, "price": price}
    else:
      index = row.index[0]
      priceCache.loc[index, "timeStamp"] = timeStamp
      priceCache.loc[index, "price"] = price

    return int(float(price) * 1e4)



# --------------------------------------------------------------
#
# --------------------------------------------------------------

def fct_exportPortfolioStatus(transactions, portfolio, priceFile=PRICE_FILE, outFile=""):

  # load price file if exist or gen new data frame
  path = Path(priceFile)

  if not path.exists():
    priceCache = pd.DataFrame(columns=["symbol", "timeStamp", "price"])
  else:
    priceCache = pd.read_csv(path, dtype={"symbol": str, "timeStamp": str, "price": float})

  # set current time
  now = datetime.now()


  with open(outFile, "w") as fid:
    fid.write("WKN     Kurz    Anzahl       akt. Kurs  Zielwert   IVST      Wert      Anstieg   (relativ)   \n")

  for wkn in portfolio:
    title           = portfolio[wkn]
    lastTransaction = transactions[title[LAST_TRANSACTION]]
    amount          = lastTransaction[AMOUNT_OF_SHARES] * 1e-6
    price           = fct_getCachedPrice(title["Symbol"], priceCache, now) * 1e-4
    title[PRICE]    = price
    ivstSum         = lastTransaction[TA_SUM] * 1e-2
    value           = amount * price
    absRaise        = value + ivstSum
    relRaise        = absRaise / abs(ivstSum) * 1e2

    outStr  = "%-6s  %-6s  " % (wkn, title["Kurz"])
    outStr += "%11.6f  " % amount
    outStr += "%9.4f  " % price
    outStr += "%9.4f  " % lastTransaction[TARGET_VALUE]
    outStr += "%8.2f  " % ivstSum
    outStr += "%8.2f  " % value
    outStr += "%+8.2f  " % absRaise
    outStr += "%+8.2f %%  " % relRaise

#    print(outStr)

    with open(outFile, "a") as fid:
      fid.write(outStr + "\n")

    portfolio[wkn]  = title

    # check for trade action demand
    if title["Typ"] in ["A", "B", "C", "D"] and lastTransaction[AMOUNT_OF_SHARES] > 0:

      actionFlag = False
      vkValue    = lastTransaction[VK_VALUE]
      outStr     = ""

      if (not actionFlag) and (value > vkValue ):
        outStr     = "VERKAUF "
        actionFlag = True
      if (not actionFlag) and (value > vkValue * (1 + SHOW_NEAR_VK_TRANSACTION_THRES)):
        outStr     = "Verkauf: %.6f x %.4f = %.2f" % (
          lastTransaction[VK_AMOUNT],
          lastTransaction[VK_PRICE],
          lastTransaction[VK_AMOUNT] * lastTransaction[VK_PRICE]
        )
        actionFlag = True

      if lastTransaction[EK_FLAG]:
        nkValue    = lastTransaction[NK_VALUE]

        if (not actionFlag) and (value < nkValue):
          outStr     = "NACHKAUF"
          actionFlag = True
        if (not actionFlag) and (value < nkValue * (1 + SHOW_NEAR_NK_TRANSACTION_THRES)):
          outStr     = "Nachkauf"
          actionFlag = True

      if actionFlag:
        with open(outFile, "a") as fid:
          fid.write(outStr + "\n")

  priceCache.to_csv(priceFile, index=False) # wirte updated price file

  return portfolio



## MAIN ###########################

# read and process input data
nPortfolio, portfolio = fct_readPfioParameters("pfioParam.md")

nTransact, transactions = fct_readTransactionsFromFile("pfioTransactionInput.md")

portfolio, transactions = fct_linkTransactions(portfolio, transactions)

transactions = fct_cummulateCnts(transactions)
transactions = fct_cummulateSums(transactions)
transactions = fct_cummulateAmountOfShares(transactions)
transactions = fct_targetValueCalculation(transactions, portfolio)
transactions = fct_finalTargetValueCalculation(transactions, portfolio)
transactions = fct_setEkFlag(transactions, portfolio)
transactions = fct_calculatedNkThres(transactions, portfolio)
transactions = fct_calculatedVkThres(transactions, portfolio)

# sort transactions by title
fct_exportTransactionsOfEachTitle(transactions, portfolio, PATH_OUTPUT_DATA + "transaktionenJedesTitelNachKuerzel/")

# process portfolio status
portfolio = fct_exportPortfolioStatus(transactions, portfolio, outFile="portfolioStatus.txt")
