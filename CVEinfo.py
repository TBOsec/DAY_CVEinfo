
import httpx,re,time,datetime
from translate import Translator


cpid = 'wwdXXXXXXXX' #企业微信的企业ID
cpsecret = 'nQVQ-jXXXXXXXXX' #企业微信自建应用的Secret
vul_like = ['weblogic','apache'] #关注的组件，可添加
risk_like = ['CRITICAL','HIGH'] #关注的威胁级别，可添加
care = 1 # 0表示只接收关注组件的漏洞，1表示所有组件的高危漏洞

# proxies = {'http': "http://127.0.0.1:7890",
#             'https': "http://127.0.0.1:7890"}

url = 'https://services.nvd.nist.gov/rest/json/cves/1.0'
headers = {
    'User-Agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:56.0) Gecko/20100101 Firefox/56.0 Waterfox/56.3',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'close',
    'Upgrade-Insecure-Requests': '1',
}
access_token = ''
content = '' #表示企业微信的文本信息

def get_cve():
    #时间比我们晚，#取三天前的漏洞才有cvss评分
    today = datetime.date.today()
    yesterday = today-datetime.timedelta(days=3)#3
    pubStartDate = str(yesterday) +'T00:00:00:000 UTC-05:00'

    if care == 1:
        for risk in risk_like:
            params = {'pubStartDate': pubStartDate,'cvssV3Severity': risk}
            with httpx.Client(params=params) as client:
                res = client.get(url).json()
            if res['totalResults'] > 0:
                res_content(res)
    else:
        for risk in risk_like:
            for vul in vul_like:
                params = {'pubStartDate': pubStartDate,'keyword': vul,'cvssV3Severity': risk}
                with httpx.Client(params=params) as client:
                    res = client.get(url).json()
                if res['totalResults'] > 0:
                    res_content(res)

        
def res_content(res):
    global content
    message = time.strftime("%Y-%m-%d", time.localtime())+'号共有`'+str(res['totalResults'])+'`个漏洞\n<font color=\"info\">下面是漏洞简介-></font>'
    send_wx(access_token,message)#每日提示消息

    for i in range(res['totalResults']):
        id = '漏洞编号：' + res['result']['CVE_Items'][i]['cve']['CVE_data_meta']['ID']+'\n'
        pubdate = '公开日期：' + res['result']['CVE_Items'][i]['publishedDate']+'\n'
        try:
            baseSeverity = '<font color="warning">漏洞等级：</font>' + res['result']['CVE_Items'][i]['impact']['baseMetricV3']['cvssV3']['baseSeverity']
            score = '<font color="warning">CVSSV3</font>：'+str(res['result']['CVE_Items'][i]['impact']['baseMetricV3']['cvssV3']['baseScore'])+'\n'
        finally:
            description = res['result']['CVE_Items'][i]['cve']['description']['description_data'][0]['value']
            description = translat(description)#翻译
            description = '漏洞描述：<font color=\"info\">' +description +'</font>\n'
            content = '**              【新增漏洞告警】**\n'+id +pubdate + baseSeverity+' '+score+description
            send_wx(access_token,content)#发送到企业微信

def translat(context): #翻译描述信息
        translator = Translator(to_lang="chinese")
        translation = translator.translate(context)
        return translation

def get_token():
    global cpid,cpsecret,access_token
    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    parms = {'corpid': cpid,'corpsecret': cpsecret}
    res = httpx.get(url,headers=headers,params=parms).json()
    errcode = res['errcode']
    if errcode != 0:
        print('something wrong:\nyou can see: https://open.work.weixin.qq.com/devtool/query?e='+ str(errcode))
    else:
        access_token = res['access_token']

def send_wx(access_token,content):
    url = "https://qyapi.weixin.qq.com/cgi-bin/appchat/send?access_token="
    data = {"chatid": "CVE",
            "msgtype":"markdown",
            "markdown":{"content" : content},
            "safe":0
            }
    res = httpx.post(url+access_token,headers=headers,json=data).json()
    errcode = res['errcode']
    if errcode != 0:
        print('something wrong:\nyou can see: https://open.work.weixin.qq.com/devtool/query?e='+ str(errcode))

def main():
    get_token()
    get_cve()
if __name__ == "__main__":
    main()