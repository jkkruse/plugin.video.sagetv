import urllib,urllib2,re
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
import os
import simplejson as json
import unicodedata
import time
from xml.dom.minidom import parse
from time import strftime
from datetime import date

__settings__ = xbmcaddon.Addon(id='plugin.video.SageTV')
__language__ = __settings__.getLocalizedString
__cwd__      = __settings__.getAddonInfo('path')

# SageTV recording Directories for path replacement
sage_rec = __settings__.getSetting("sage_rec")
sage_unc = __settings__.getSetting("sage_unc")

# SageTV URL based on user settings
strUrl = 'http://' + __settings__.getSetting("sage_user") + ':' + __settings__.getSetting("sage_pass") + '@' + __settings__.getSetting("sage_ip") + ':' + __settings__.getSetting("sage_port")
iconImage = xbmc.translatePath(os.path.join(__cwd__,'resources','media','icon.png'))
DEFAULT_CHARSET = 'utf-8'

def TOPLEVELCATEGORIES():
 
	addTopLevelDir('[Watch Recordings]', strUrl + '/',1,iconImage,'Browse previously recorded and currently recording shows')
	addTopLevelDir('[View Upcoming Recordings]', strUrl + '/sagex/api?command=GetScheduledRecordings&encoder=json',2,iconImage,'View and manage your upcoming recording schedule')
	
def WATCHRECORDINGS(url,name):
	#Get the list of Recorded shows
	addDir('[All Shows]', strUrl + '/sage/Recordings?xml=yes',11,iconImage,'')
	req = urllib.urlopen(strUrl + '/sage/Recordings?xml=yes')
	content = parse(req)
	dictOfTitlesAndMediaFileIds = {}
	dictOfTitlesAndExternalIds = {}
	for showlist in content.getElementsByTagName('show'):
		strTitle = ''
		strMediaFileId = ''
		strExternalId = ''
		for shownode in showlist.childNodes:
			strExternalId = showlist.getAttribute('epgId')
			# Get the title of the show
			if shownode.nodeName == 'title':
				strTitle = shownode.toxml()
				strTitle = strTitle.replace('<title>','')
				strTitle = strTitle.replace('</title>','')
				strTitle = strTitle.replace('&amp;','&')
				strTitle = strTitle.replace('&quot;','"')
				strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
			# Get the mediafileid of the show
			if shownode.nodeName == 'airing':
				for shownode1 in shownode.childNodes:
					if shownode1.nodeName == 'mediafile':
						strMediaFileId = shownode1.getAttribute('sageDbId')

			if(strTitle<>""):
				dictOfTitlesAndMediaFileIds[strTitle] = strMediaFileId
				dictOfTitlesAndExternalIds[strTitle] = strExternalId

	for strTitle in dictOfTitlesAndMediaFileIds:
		urlToShowEpisodes = strUrl + '/sage/Search?searchType=TVFiles&SearchString=' + urllib2.quote(strTitle.encode("utf8")) + '&DVD=on&sort2=airdate_asc&partials=both&TimeRange=0&pagelen=100&sort1=title_asc&filename=&Video=on&search_fields=title&xml=yes'
		print "ADDING strTitle=" + strTitle + "; urlToShowEpisodes=" + urlToShowEpisodes
		imageUrl = strUrl + "/sagex/media/poster/" + dictOfTitlesAndMediaFileIds[strTitle]
		#print "ADDING imageUrl=" + imageUrl
		addDir(strTitle, urlToShowEpisodes,11,imageUrl,dictOfTitlesAndExternalIds[strTitle])

def VIDEOLINKS(url,name):
        #Videolinks gets called immediately after adddir, so the timeline is categories, adddir, and then videolinks
        #Videolinks then calls addlink in a loop
        #This code parses the xml link
        req = urllib.urlopen(url)
        try:
          content = parse(req)
          print "# of EPISODES for " + name + "=" + str(content.getElementsByTagName('show').length)
          if(content.getElementsByTagName('show').length == 0):
            print "NO EPISODES FOUND FOR SHOW=" + name
            xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=True)
            return
        except:
          print "NO EPISODES FOUND FOR SHOW=" + name
          xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=True)
          return

        for showlist in content.getElementsByTagName('show'):
          strTitle = ''
          strEpisode = ''
          strDescription = ''
          strGenre = ''
          strOriginalAirdate = ''
          strAiringdate = ''
          strMediaFileID = ''
          strAiringID = ''
          for shownode in showlist.childNodes:
            # Get the title of the show
            if shownode.nodeName == 'title':
              strTitle = shownode.toxml()
              strTitle = strTitle.replace('<title>','')
              strTitle = strTitle.replace('</title>','')
              strTitle = strTitle.replace('&amp;','&')
            # Get the episode name
            if shownode.nodeName == 'episode':
              strEpisode = shownode.toxml()
              strEpisode = strEpisode.replace('<episode>','')
              strEpisode = strEpisode.replace('</episode>','')
              strEpisode = strEpisode.replace('&amp;','&')
            # Get the show description
            if shownode.nodeName == 'description':
              strDescription = shownode.toxml()
              strDescription = strDescription.replace('<description>','')
              strDescription = strDescription.replace('</description>','')
              strDescription = strDescription.replace('&amp;','&')
            # Get the category to use for genre
            if shownode.nodeName == 'category':
              strGenre = shownode.toxml()
              strGenre = strGenre.replace('<category>','')
              strGenre = strGenre.replace('</category>','')
              strGenre = strGenre.replace('&amp;','&')
            # Get the airdate to use for Aired
            if shownode.nodeName == 'originalAirDate':
              strOriginalAirdate = shownode.toxml()
              strOriginalAirdate = strOriginalAirdate.replace('<originalAirDate>','')
              strOriginalAirdate = strOriginalAirdate.replace('</originalAirDate>','')
              strOriginalAirdate = strOriginalAirdate[:10]
              # now that we have the title, episode, genre and description, create a showname string depending on which ones you have
              # if there is no episode name use the description in the title
            if len(strEpisode) == 0:
              strShowname = strTitle+' - '+strDescription
              strPlot = strDescription
              # else if there is an episode use that
            elif len(strEpisode) > 0:
              if name == '[All Shows]' or name == 'Sports': 
                strShowname = strTitle+' - '+strEpisode
              elif name != '[All Shows]' and name != 'Sports':
                strShowname = strEpisode
              strPlot = strDescription
            if shownode.nodeName == 'airing':
              strAiringID = shownode.getAttribute('sageDbId')
            # Get the airdate to use for Aired
              strAiringdate = shownode.getAttribute('startTime')
              strAiringdate = strAiringdate[:10]
              for shownode1 in shownode.childNodes:
                if shownode1.nodeName == 'mediafile':
                  strMediaFileID = shownode1.getAttribute('sageDbId')
                  for shownode2 in shownode1.childNodes:
                    if shownode2.nodeName == 'segmentList':
                      shownode3 =  shownode2.childNodes[1]
                      strFilepath = shownode3.getAttribute('filePath')
                      addMediafileLink(strShowname,strFilepath.replace(sage_rec, sage_unc),strPlot,'',strGenre,strOriginalAirdate,strAiringdate,strTitle,strMediaFileID,strAiringID)

def VIEWUPCOMINGRECORDINGS(url,name):
	#req = urllib.urlopen(url)
	airings = executeSagexAPIJSONCall(url, "Result")
	for airing in airings:
		show = airing.get("Show")
		strTitle = airing.get("AiringTitle")
		strEpisode = show.get("ShowEpisode")
		if(strEpisode == None):
			strEpisode = ""		
		strDescription = show.get("ShowDescription")
		if(strDescription == None):
			strDescription = ""		
		strGenre = show.get("ShowCategoriesString")
		strAiringID = str(airing.get("AiringID"))
		seasonNum = int(show.get("ShowSeasonNumber"))
		episodeNum = int(show.get("ShowEpisodeNumber"))
		
		startTime = float(airing.get("AiringStartTime") // 1000)
		strAiringdateObject = date.fromtimestamp(startTime)
		airTime = strftime('%H:%M', time.localtime(startTime))
		strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.month, strAiringdateObject.day, strAiringdateObject.year)
		strOriginalAirdate = strAiringdate
		if(airing.get("OriginalAiringDate")):
			startTime = float(airing.get("OriginalAiringDate") // 1000)
			strOriginalAirdate = date.fromtimestamp(startTime)
			strOriginalAirdate = str(strOriginalAirdate.month) + '.' + str(strOriginalAirdate.day) + '.' + str(strOriginalAirdate.year)

		# if there is no episode name use the description in the title
		if(strEpisode == ""):
			strDisplayText = strTitle + ' - ' + strDescription
		# else if there is an episode use that
		else:
			strDisplayText = strTitle + ' - ' + strEpisode
		strDisplayText = strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime + ": " + strDisplayText
		addAiringLink(strDisplayText,'',strDescription,'',strGenre,strOriginalAirdate,strAiringdate,strTitle,strAiringID,seasonNum,episodeNum)

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

def addMediafileLink(name,url,plot,iconimage,genre,originalairingdate,airingdate,showtitle,mediafileid,airingid):
        ok=True
        liz=xbmcgui.ListItem(name)
        scriptToRun = "special://home/addons/plugin.video.SageTV/contextmenuactions.py"
        actionDelete = "delete|" + strUrl + '/sagex/api?command=DeleteFile&1=mediafile:' + mediafileid
        actionCancelRecording = "cancelrecording|" + strUrl + '/sagex/api?command=CancelRecord&1=mediafile:' + mediafileid
        actionRemoveFavorite = "removefavorite|" + strUrl + '/sagex/api?command=EvaluateExpression&1=RemoveFavorite(GetFavoriteForAiring(GetAiringForID(' + airingid + ')))'
        bisAiringRecording = isAiringRecording(airingid)
        bisFavorite = isFavorite(airingid)
        if(bisAiringRecording == "true"):
          if(bisFavorite == "true"):
            liz.addContextMenuItems([('Delete Show', 'XBMC.RunScript(' + scriptToRun + ', ' + actionDelete + ')'), ('Cancel Recording', 'XBMC.RunScript(' + scriptToRun + ', ' + actionCancelRecording + ')'), ('Remove Favorite', 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')')], True)
          else:
            liz.addContextMenuItems([('Delete Show', 'XBMC.RunScript(' + scriptToRun + ', ' + actionDelete + ')'), ('Cancel Recording', 'XBMC.RunScript(' + scriptToRun + ', ' + actionCancelRecording + ')')], True)
        else:
          if(bisFavorite == "true"):
            liz.addContextMenuItems([('Delete Show', 'XBMC.RunScript(' + scriptToRun + ', ' + actionDelete + ')'), ('Remove Favorite', 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')')], True)
          liz.addContextMenuItems([('Delete Show', 'XBMC.RunScript(' + scriptToRun + ', ' + actionDelete + ')')], True)
        datesplit = originalairingdate.split('-')
        try:
            originalairingdate = datesplit[2]+'.'+datesplit[1]+'.'+datesplit[0]
        except:
            originalairingdate = ""
        datesplit = airingdate.split('-')
        try:
            airingdate = datesplit[2]+'.'+datesplit[1]+'.'+datesplit[0]
        except:
            airingdate = "01.01.1900"
        seasonnum = int(executeSagexAPICall(strUrl + '/sagex/api?command=GetShowSeasonNumber&1=airing:' + airingid, "Result"))
        episodenum = int(executeSagexAPICall(strUrl + '/sagex/api?command=GetShowEpisodeNumber&1=airing:' + airingid, "Result"))
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot, "Genre": genre, "date": airingdate, "premiered": originalairingdate, "aired": originalairingdate, "TVShowTitle": showtitle, "season": seasonnum, "episode": episodenum } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
        return ok

def addAiringLink(name,url,plot,iconimage,genre,originalairingdate,airingdate,showtitle,airingid,seasonnum,episodenum):
	ok=True
	liz=xbmcgui.ListItem(name)
	scriptToRun = "special://home/addons/plugin.video.SageTV/contextmenuactions.py"
	#actionCancelRecording = "cancelrecording|" + strUrl + '/sagex/api?command=CancelRecord&1=mediafile:' + mediafileid
	actionRemoveFavorite = "removefavorite|" + strUrl + '/sagex/api?command=EvaluateExpression&1=RemoveFavorite(GetFavoriteForAiring(GetAiringForID(' + airingid + ')))'
	bisFavorite = isFavorite(airingid)
	if(bisFavorite == "true"):
		liz.addContextMenuItems([('Remove Favorite', 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')')], True)
	print "originalairingdate=" + originalairingdate + ";airingdate=" + airingdate
	liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot, "Genre": genre, "date": airingdate, "premiered": originalairingdate, "aired": originalairingdate, "TVShowTitle": showtitle, "season": seasonnum, "episode": episodenum } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
	return ok

# Checks if an airing is currently recording
def isAiringRecording(airingid):
	sageApiUrl = strUrl + '/sagex/api?command=IsFileCurrentlyRecording&1=airing:' + airingid
	return executeSagexAPICall(sageApiUrl, "Result")
		
# Checks if an airing has a favorite set up for it
def isFavorite(airingid):
	sageApiUrl = strUrl + '/sagex/api?command=IsFavorite&1=airing:' + airingid
	return executeSagexAPICall(sageApiUrl, "Result")
		
# Checks if an airing has a favorite set up for it
def getShowSeriesDescription(showexternalid):
	sageApiUrl = strUrl + '/sagex/api?command=EvaluateExpression&1=GetSeriesDescription(GetShowSeriesInfo(GetShowForExternalID("' + showexternalid + '")))'
	return executeSagexAPICall(sageApiUrl, "Result")
		
def executeSagexAPICall(url, resultToGet):
	#Log.Debug('*** sagex request URL: %s' % url)
	try:
		print "CALLING sageApiUrl=" + url
		input = urllib.urlopen(url)
	except IOError, i:
		print "ERROR in executeSagexAPICall: Unable to connect to SageTV server"
		return None

	content = parse(input)
	result = content.getElementsByTagName(resultToGet)[0].toxml()
	result = result.replace("<" + resultToGet + ">","")
	result = result.replace("</" + resultToGet + ">","")
	result = result.replace("<![CDATA[","")
	result = result.replace("]]>","")
	result = result.replace("<Result/>","")
	return result

def executeSagexAPIJSONCall(url, resultToGet):
	print "*** sagex request URL:" + url
	try:
		input = urllib.urlopen(url)
	except IOError, i:
		print "ERROR in executeSagexAPIJSONCall: Unable to connect to SageTV server"
		return None
	fileData = input.read()
	resp = unicodeToStr(json.JSONDecoder().decode(fileData))

	objKeys = resp.keys()
	numKeys = len(objKeys)
	if(numKeys == 1):
		return resp.get(resultToGet)
	else:
		return None

def addTopLevelDir(name,url,mode,iconimage,dirdescription):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name)

	liz.setInfo(type="video", infoLabels={ "Title": name, "Plot": dirdescription } )
	liz.setIconImage(iconimage)
	liz.setThumbnailImage(iconimage)
	#liz.setIconImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
	#liz.setThumbnailImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok

def addDir(name,url,mode,iconimage,showexternalid):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name)
	strSeriesDescription = ""
	strSeriesDescription = getShowSeriesDescription(showexternalid)

	liz.setInfo(type="video", infoLabels={ "Title": name, "Plot": strSeriesDescription } )
	liz.setIconImage(iconimage)
	liz.setThumbnailImage(iconimage)
	#liz.setIconImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
	#liz.setThumbnailImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok


def unicodeToStr(obj):
	t = obj
	if(t is unicode):
		return obj.encode(DEFAULT_CHARSET)
	elif(t is list):
		for i in range(0, len(obj)):
			obj[i] = unicodeToStr(obj[i])
		return obj
	elif(t is dict):
		for k in obj.keys():
			v = obj[k]
			del obj[k]
			obj[k.encode(DEFAULT_CHARSET)] = unicodeToStr(v)
		return obj
	else:
		return obj # leave numbers and booleans alone

	
params=get_params()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

if mode==None or url==None or len(url)<1:
        print ""
        TOPLEVELCATEGORIES()
       
elif mode==1:
        print ""+url
        WATCHRECORDINGS(url,name)
        
elif mode==11:
        print ""+url
        VIDEOLINKS(url,name)
        
elif mode==2:
        print ""+url
        VIEWUPCOMINGRECORDINGS(url,name)

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)
xbmcplugin.setContent(int(sys.argv[1]),'episodes')
xbmcplugin.endOfDirectory(int(sys.argv[1]))