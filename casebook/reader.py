#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

# Copyright (c) Valentin Fedulov <vasnake@gmail.com>
# See COPYING for details.

''' casebook reader module

'''

import simplejson
import requests
import requests.utils
import pickle
import os

import casebook
import casebook.http
import casebook.messages

CP = casebook.CP

USERNAME = os.environ.get("CASEBOOK_USER", "casebook.ru account username")
PASSWORD = os.environ.get("CASEBOOK_PASSWORD", "secret")
DATA_DIR = os.environ.get("CASEBOOK_DATA", "/tmp")

COMMON_HEADERS = {"Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 5.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.149 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "x-date-format": "iso",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Proxy-Connection": "keep-alive",
    "Referer": "http://casebook.ru/"}

CASES_QUERY_TEMPLATE = u'''
    {"StatusEx":[],"SideTypes":[],"ConsiderType":-1,"CourtType":-1,"CaseNumber":null,"CaseCategoryId":"",
        "MonitoredStatus":-1,"Courts":[],"Instances":[],"Judges":[],
        "Delegate":"","StateOrganizations":[],"DateFrom":null,"DateTo":null,"SessionFrom":null,"SessionTo":null,
        "FinalDocFrom":null,"FinalDocTo":null,"MinSum":0,"MaxSum":-1,
        "Sides":[],"CoSides":[],"JudgesNames":[],
        "Accuracy":2,
        "Page":1,
        "Count":30,
        "OrderBy":"incoming_date_ts desc",
        "Query":"ОАО ГАЗПРОМБАНК"}
'''


def main():
    session = casebook.http.HttpSession()
    session.restoreCookies(os.path.join(DATA_DIR, '.session'))
    session.setHeaders(COMMON_HEADERS)

    # check access
    url = 'http://casebook.ru/api/Message/UnreadCount?'
    res = session.get(url)
    print (u"%s: %s" % (url, res.text)).encode(CP)
    js = casebook.messages.JsonResponce(res.text)
    if js.Success:
        print 'we good'
    else:
        print (u"Auth. need to be done. Message: %s" % js.Message).encode(CP)
        session = logon(session, USERNAME, PASSWORD)

    # read input and make queries
    inputFileName = os.path.join(DATA_DIR, 'input.lst')
    with open(inputFileName) as f:
        for x in f:
            x = x.decode(CP).strip()
            print (u"input: '%s'" % x).encode(CP)
            if x and x[0] != u'#':
                getCasesAndSides(session, x)

    session.saveCookies()
    print "that's all for now"


def getCasesAndSides(session, queryString):
    '''Perform queries to casebook.ru
        POST http://casebook.ru/api/Search/Cases
        GET http://casebook.ru/api/Search/Sides

    Print results, save results

    Результат каждого запроса сохраняется в файл по шаблону:
        data/query.{hash}.(cases|sides).json
    Дополнительно, информация о запросе/ответе сохраняется в индексный файл:
        index.json
    '''
    jsCases = findCases(session, queryString)
    jsSides = findSides(session, queryString)

    forEachCase(session, jsCases)
    # TODO:
    #~ forEachSide(session, jsSides)


def forEachCase(session, jsCases):
    '''Collect information for each case
    '''
    numCases = int(jsCases.obj[u'Result'][u'TotalCount'])
    print "forEachCase, TotalCount %s" % numCases
    if numCases <= 0:
        return

    casesList = jsCases.obj[u'Result'][u'Items']
    for case in casesList:
        collectCaseData(session, case)


def collectCaseData(session, case):
    '''Collect information for given case
    '''
    CaseId = case[u"CaseId"]
    print "collectCaseData, CaseId %s" % CaseId
    #~ карточка дела GET http://casebook.ru/api/Card/Case?id=78d283d0-010e-4c50-b1d1-cf2395c00bf9
    jsCardCase = cardCase(session, CaseId)
    # TODO:
    #~ документы
    #~ участники


def cardCase(session, CaseId):
    '''Get Card/Case data from http://casebook.ru/api/Card/Case
    and save results.
    Returns messages.JsonResponce with casebook message
    '''
    print u"Card/Case by CaseId '%s' ..." % CaseId

    url = 'http://casebook.ru/api/Card/Case'
    payload = {'id': CaseId}
    res = session.get(url, params=payload)

    print (u"%s: %s" % (url, res.text)).encode(CP)
    jsCardCase = parseResponce(res.text)

    saveCardCase(jsCardCase, CaseId)
    return jsCardCase


def findSides(session, queryString):
    '''Find sides via http://casebook.ru/api/Search/Sides
    and save results.
    Returns messages.JsonResponce with casebook message
    '''
    print (u"sidesBy '%s' ..." % queryString).encode(CP)

    url = 'http://casebook.ru/api/Search/Sides'
    payload = {'name': queryString}
    res = session.get(url, params=payload)

    print (u"%s: %s" % (url, res.text)).encode(CP)
    jsSides = parseResponce(res.text)

    #~ Результат каждого запроса сохраняется в файл по шаблону:
    #~ data/query.{hash}.(cases|sides).json
    fname = saveSidesSearch(jsSides, queryString)
    #~ Дополнительно, информация о запросе/ответе сохраняется в индексный файл:
    #~ index.json
    updateIndexForSidesSearch(queryString, fname, jsSides)
    return jsSides


def findCases(session, queryString):
    '''Find cases via POST http://casebook.ru/api/Search/Cases
    and save results.
    Returns messages.JsonResponce with casebook message
    '''
    print (u"casesBy '%s' ..." % queryString).encode(CP)

    url = 'http://casebook.ru/api/Search/Cases'
    qt = CASES_QUERY_TEMPLATE
    payload = simplejson.loads(qt)
    payload[u"Query"] = queryString
    res = session.post(url, data=simplejson.dumps(payload))

    print (u"%s: %s" % (url, res.text)).encode(CP)
    jsCases = parseResponce(res.text)

    #~ Результат каждого запроса сохраняется в файл по шаблону:
    #~ data/query.{hash}.(cases|sides).json
    fname = saveCasesSearch(jsCases, queryString)
    #~ Дополнительно, информация о запросе/ответе сохраняется в индексный файл:
    #~ index.json
    updateIndexForCasesSearch(queryString, fname, jsCases)
    return jsCases


def saveCardCase(jsCardCase, CaseId):
    '''Save case data to file, update index
    '''
    fname = saveResults2File(jsCardCase, CaseId, 'card', 'case')
    updateIndexForCase(CaseId, fname, jsCardCase)


def saveCasesSearch(jsResp, queryString):
    '''Save search results to file.
    Returns file name
    '''
    return saveSearchResults2File(jsResp, queryString, 'cases')

def saveSidesSearch(jsResp, queryString):
    '''Save search results to file.
    Returns file name
    '''
    return saveSearchResults2File(jsResp, queryString, 'sides')

def saveSearchResults2File(jsResp, queryString, typeName):
    '''Save search results to file.
    Returns file name
    '''
    return saveResults2File(jsResp, queryString, 'query', typeName)

def saveResults2File(jsResp, queryString, category, typeName):
    '''Save search results to file.
    Returns file name
    '''
    id = stringToFileName(queryString)
    fname = os.path.join(DATA_DIR, "%s.%s.%s.json" % (category, id, typeName))
    print (u"write result to file '%s'" % fname).encode(CP)

    with open(fname, 'wb') as f:
        f.write(jsResp.text.encode(CP))
    return fname


def updateIndexForCase(CaseId, fname, jsCardCase):
    '''Save case id and file name to index.json file
    '''
    indexObj = loadIndex()
    caseMeta = getCaseMetaFromIndex(indexObj, CaseId)

    caseMeta["CaseId"] = CaseId
    caseMeta["Number"] = jsCardCase.obj[u'Result'][u'Case'][u'Number']
    caseMeta["FileName"] = fname
    caseMeta["Error"] = jsCardCase.Message if jsCardCase.Success == False else ''
    caseMeta["Warning"] = jsCardCase.Message

    indexObj = setCaseMetaToIndex(indexObj, CaseId, caseMeta)
    saveIndex(indexObj)


def updateIndexForSidesSearch(queryString, fname, jsSides):
    '''Save queries result metadata to index.json file
    '''
    indexObj = loadIndex()
    qryResults = getQueryResFromIndex(indexObj, queryString)

    qryResults["qryString"] = queryString
    qryResults["sidesRespFile"] = fname
    qryResults["sidesRespError"] = jsSides.Message if jsSides.Success == False else ''
    qryResults["sidesRespWarning"] = jsSides.Message
    qryResults["sidesCount"] = len(jsSides.obj[u'Result'])

    indexObj = setQueryResToIndex(indexObj, queryString, qryResults)
    saveIndex(indexObj)


def updateIndexForCasesSearch(queryString, fname, jsCases):
    '''Save queries result metadata to index.json file
    '''
    indexObj = loadIndex()
    qryResults = getQueryResFromIndex(indexObj, queryString)

    qryResults["qryString"] = queryString
    qryResults["casesRespFile"] = fname
    qryResults["casesRespError"] = jsCases.Message if jsCases.Success == False else ''
    qryResults["casesRespWarning"] = jsCases.Message
    qryResults["casesCount"] = int(jsCases.obj[u'Result'][u'TotalCount'])

    indexObj = setQueryResToIndex(indexObj, queryString, qryResults)
    saveIndex(indexObj)


def setCaseMetaToIndex(indexObj, CaseId, caseMeta):
    '''Set index.cases.{CaseId} to caseMeta.
    Returns updated indexObj
    '''
    return setListItemToIndex(indexObj, 'cases', CaseId, caseMeta)

def setQueryResToIndex(indexObj, queryString, qryResults):
    '''Set index.queries.{queryString} to qryResults.
    Returns updated indexObj
    '''
    return setListItemToIndex(indexObj, 'queries', queryString, qryResults)
    #~ idxQryList = indexObj.get('queries', {})
    #~ idxQryList[queryString] = qryResults
    #~ indexObj['queries'] = idxQryList
    #~ return indexObj

def setListItemToIndex(indexObj, listName, itemName, data):
    '''Set index.{listName}.{itemName} to data.
    Returns updated indexObj
    '''
    idxList = indexObj.get(listName, {})
    idxList[itemName] = data
    indexObj[listName] = idxList
    return indexObj


def  getCaseMetaFromIndex(indexObj, CaseId):
    '''Returns index.cases.{CaseId} dictionary from index
    '''
    return getListItemFromIndex(indexObj, 'cases', CaseId)

def getQueryResFromIndex(indexObj, queryString):
    '''Returns index.queries.{queryString} dictionary from index
    '''
    return getListItemFromIndex(indexObj, 'queries', queryString)
    #~ idxQryList = indexObj.get('queries', {})
    #~ qryResults = idxQryList.get(queryString, {})
    #~ return qryResults

def getListItemFromIndex(indexObj, listName, itemName):
    '''Returns index.{listName}.{itemName} dictionary from index
    '''
    idxList = indexObj.get(listName, {})
    return idxList.get(itemName, {})


def loadIndex():
    '''Returns indexObj = simplejson.loads(indexText from index.json file)
    '''
    indexFname = os.path.join(DATA_DIR, "index.json")
    indexText = u"{}"
    if os.path.isfile(indexFname):
        with open(indexFname) as f:
            indexText = f.read().strip().decode(CP)
    return simplejson.loads(indexText)


def saveIndex(indexObj):
    '''Save obj to index.json file
    simplejson.dumps(indexObj, sort_keys=True, indent='  ', ensure_ascii=False)
    '''
    txt = simplejson.dumps(indexObj, sort_keys=True, indent='  ', ensure_ascii=False)
    with open(os.path.join(DATA_DIR, "index.json"), 'wb') as f:
        f.write(txt.encode(CP))


def stringToFileName(aStr):
    '''Make a string good for file name
    '''
    return getHashString(aStr.encode(CP))


def getHashString(aStr):
    '''Returns string as hashlib.sha1(aStr).hexdigest().
    aStr must be non-unicode string
    '''
    import hashlib
    return hashlib.sha1(aStr).hexdigest()


def parseResponce(text):
    '''Print results status message.
    Returns casebook.messages.JsonResponce
    '''
    js = casebook.messages.JsonResponce(text)
    if js.Success and js.Message == u'':
        print 'we good'
    else:
        err = u"Request failed. Message: %s" % js.Message
        print err.encode(CP)
        raise casebook.RequestError(err)
    return js


def logon(session, username, password):
    '''Perform LogOn requests on casebook.ru
    If logon isn't successfull raise an casebook.LogOnError exception
    '''
    print "logon..."
    url = 'http://casebook.ru/api/Account/LogOn'
    payload = {"SystemName": "Sps","UserName": username,"Password": password,"RememberMe": True}
    session.deleteCookies()
    res = session.post(url, data=simplejson.dumps(payload))
    print (u"%s: %s" % (url, res.text)).encode(CP)
    js = casebook.messages.JsonResponce(res.text)
    if js.Success:
        print 'we good'
    else:
        err = u"Auth failed. Message: %s" % js.Message
        print err.encode(CP)
        raise casebook.LogOnError(err)

    return session
