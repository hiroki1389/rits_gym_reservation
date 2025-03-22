const replURK = "your_replit_url" // ここにreplitのURLを代入する

const keepRepl = () => {
  const replURL = PropertiesService.getScriptProperties().getProperty('replURL')
  const data = {}
  const headers = { 'Content-Type': 'application/json; charset=UTF-8' }
  const params = {
    method: 'post',
    payload: JSON.stringify(data),
    headers: headers,
    muteHttpExceptions: true
  }

  response = UrlFetchApp.fetch(replURL, params);
  console.log(response)
}