import numpy as np
import pandas as pd

def getPivot(data,index,interval=2):
    resp = {
        "message": None,
        "index":data.at[index,"time"],
        "startIndex": data.at[index - interval,"time"],
        "endIndex": data.at[index + interval,"time"],
        "interval":interval,
        "isSwingHigh": None,
        "isSwingLow": None,
        "valid" : False,
        # "before": [],
        # "after":[]
    }
    df=data.copy()
    start = index - interval 
    end = index + interval 
    sliceData = []
    current={}
    before=[]
    after=[]

    if start >= 0 and end < len(df):
        sliceData = df.loc[start:end, ['time',"high", "low"]]  # end+1 because slicing is exclusive
    else:
        resp["message"] = f"Cannot slice - would go out of bounds (start: {start}, end: {end}, df length: {len(df)})"

    if resp["message"] == None:
        # current = sliceData.iloc[index]
        current = sliceData[sliceData.index==index]
        # All Highs before current index
        before = sliceData.loc[:index - 1 ]
        # resp["before"] = sliceData.loc[:index - 1 ]
        # All Highs after current index
        after = sliceData.loc[index + 1:]
        # resp["after"] = sliceData.loc[index + 1:]

        resp["isSwingHigh"] =  current['high'].item() if (current['high'].item()>before['high'].max().item()) and (current['high'].item()>after["high"].max().item()) else None
        resp["isSwingLow"] = current['low'].item() if (current['low'].item()<before['low'].min().item()) and (current['low'].item()<after["low"].min().item()) else None
        
        if resp["isSwingHigh"] or resp["isSwingLow"]:
            resp["valid"] = True
    # print(sliceData)
    return resp

def getPivots(data,interval=2,beginIndex=None,stopIndex=None):

    resp={
        "message":None,
        "data":[],
        "start_idx" : data.at[interval,"time"],
        "end_idx" : data.at[len(data) - interval - 1,"time"],
        "interval":interval,
        "beginIndex": beginIndex,
        "stopIndex":stopIndex

    }
    
    start_idx = interval
    end_idx = len(data) - interval 
    minLen = (interval*2)+1

    if (minLen>len(data)):
        resp["message"]=f"Data only has length of {len(data)} which is min length is {minLen}"
        return resp
        

    if beginIndex :
        if beginIndex>start_idx and (( end_idx-beginIndex)>=minLen):
            start_idx=beginIndex
        
    
    if stopIndex and (( stopIndex-start_idx)>=minLen):
        if stopIndex<end_idx:
            end_idx=stopIndex

    for idx in range(start_idx, end_idx ):
        result = getPivot(data, idx, interval)
        resp["data"].append(result)
    
    return resp

def getSwingHighBreakDf(swings,data):
    resp =swings.copy()
    resp['breakHigh'] = [None]*len(resp)
    for idx in range(0, len(swings) ):
        testHigh=swings.iloc[idx][["time","value"]]
        res= data[(data["close"] > testHigh["value"]) & (data['time'] > testHigh['time'])]['time']
        if len(res)>0 :
            resp.loc[resp['value']==testHigh['value'],'breakHigh']=res.iloc[0]
    return resp

def getSwingHighBreak(swings,data):
    # resp =swings.copy()
    # resp['breakHigh'] = [None]*len(resp)
    resp=list()
    for idx in range(0, len(swings) ):
        testHigh=swings.iloc[idx][["value","time"]]
        res= data[(data["close"] > testHigh["value"]) & (data['time'] > testHigh['time'])]['time']
        if len(res)>0 :
            resp.append({"p1":{"time":testHigh["time"].item(),"price":testHigh["value"].item()},"p2":{"time":res.iloc[0].item(),"price":testHigh["value"].item()}})
    return resp

def getSwingLowBreak(swings,data):
    # resp =swings.copy()
    # resp['breakLow'] = [None]*len(resp)
    resp=list()
    for idx in range(0, len(swings) ):
        # print(swings.iloc[idx])
        testLow=swings.iloc[idx][["value","time"]]
        res= data[(data["close"] < testLow["value"]) & (data['time'] > testLow['time'])]['time']
        if len(res)>0 :
            resp.append({"p1":{"time":testLow["time"].item(),"price":testLow["value"].item() },"p2":{"time":res.iloc[0].item(),"price":testLow["value"].item() }})
    return resp

def getSwingLowBreakDf(swings,data):
    resp =swings.copy()
    resp['breakLow'] = [None]*len(resp)
    for idx in range(0, len(swings) ):
        testLow=swings.iloc[idx][["value","time"]]
        res= data[(data["close"] < testLow["value"]) & (data['time'] > testLow['time'])]['time']
        if len(res)>0 :
            resp.loc[resp['time']==testLow['time'],'breakLow']=res.iloc[0]
    return resp

def getSwingBreaks(data,interval=2,beginIndex=None,stopIndex=None):

    resp={
        "message":None,
        "data":{},
        "start_idx" : data.at[interval,"time"],
        "end_idx" : data.at[len(data) - interval - 1,"time"],
        "interval":interval,
        "beginIndex": beginIndex,
        "stopIndex":stopIndex

    }
    swingData= getPivots(data)

    if swingData["message"] != None:
        resp["message"] = swingData["message"]
        return resp
    df = pd.DataFrame(swingData['data'])

    dfSwingHigh=df[df['isSwingHigh'].notna()][['index','startIndex','endIndex','isSwingHigh']]
    dfSwingHigh.rename(columns={'index': 'time', 'isSwingHigh': 'value'}, inplace=True)

    dfSwingLow=df[df['isSwingLow'].notna()][['index','startIndex','endIndex','isSwingLow']]
    dfSwingLow.rename(columns={'index': 'time', 'isSwingLow': 'value'}, inplace=True)

    breakLow=getSwingLowBreak(dfSwingLow,data)
    breakHigh = getSwingHighBreak(dfSwingHigh,data)

    resp["data"] = {
        "breakLow":pd.DataFrame(breakLow).to_dict(orient='records'),
        "breakHigh":pd.DataFrame(breakHigh).to_dict(orient='records')
    }
    return resp

def getGap(data,index):
    resp = {
        "message": None,
        "index":data.at[index,"time"],
        'isBuy':False,
        'isGap':False,
        "Pre": None,
        "Post": None,
        "valid" : False,
        # "before": [],
        # "after":[]
    }
    df=data.copy()
    current={}
    before=[]
    after=[]

    current = df.iloc[index]

    # All Highs before current index
    before = df.iloc[index - 1 ]
    # resp["before"] = sliceData.loc[:index - 1 ]
    # All Highs after current index
    after = df.iloc[index + 1]
    # resp["after"] = sliceData.loc[index + 1:]
    if(current["open"]<current['close']):
        resp['isBuy']=True
        # resp['isGap'] = before['high']<after['low'] and not before["open"]> before["close"]
        resp['isGap'] = before['high']<after['low'] 
        if resp["isGap"]:
            resp["Pre"] = before['high']
            resp["Post"] =after['low']
    else:
        # resp['isGap'] = before['low']>after['high']  and not before["open"]< before["close"]
        resp['isGap'] = before['low']>after['high']  

        if resp["isGap"]:
            resp["Pre"] = before['low']
            resp["Post"] =after['high']
    
    if resp["isGap"]:
        resp["valid"] = True
    return resp    

def getGapEnd(data,result):
    resp = {
        "message": None,
        "index":result["index"].item(),
        'isBuy':result['isBuy'],
        "Pre": result['Pre'].item(),
        "Post": result['Post'].item(),
        "end" : None,
        # "before": [],
        # "after":[]
    }


    if result["isBuy"] :
        res= data[(data["close"] < result["Pre"]) & (data['time'] > result["index"])]['time']
    else:
        res= data[(data["close"] > result["Pre"]) & (data['time'] > result["index"])]['time']
    if len(res)>0 :
        resp['end']=res.iloc[0].item()
    else:
        resp['end']=data.iloc[-1]['time'].item()
    
    return resp

def getGaps(data):

    resp={
        "message":None,
        "data":[],
    }
    
    start_idx = 1
    end_idx = len(data) - 1 
    minLen = 3

    if (minLen>len(data)):
        resp["message"]=f"Data only has length of {len(data)} which is min length is {minLen}"
        return resp
        

    for idx in range(start_idx, end_idx ):
        result = getGap(data, idx)
        if result['isGap']:
            resp["data"].append(getGapEnd(data,result))
    
    return resp

def calculate_rsi(data, periods=14):
    """
    Calculate the Relative Strength Index (RSI) for a given OHLC dataset.
    
    Parameters:
        data (pd.DataFrame): DataFrame with 'Close' prices.
        periods (int): Lookback period for RSI (default=14).
    
    Returns:
        pd.Series: RSI values.
    """
    # Calculate price changes
    delta = data['Close'].diff()
    
    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Calculate average gains and losses (SMA)
    avg_gain = gain.rolling(window=periods).mean()
    avg_loss = loss.rolling(window=periods).mean()
    
    # Calculate Relative Strength (RS)
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    return rsi