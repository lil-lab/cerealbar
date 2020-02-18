function getBrowser() {
  var ua=navigator.userAgent,tem,M=ua.match(/(opera|chrome|safari|firefox|msie|trident(?=\/))\/?\s*(\d+)/i) || []; 
  if(/trident/i.test(M[1])){
    tem=/\brv[ :]+(\d+)/g.exec(ua) || []; 
    return {name:'IE',version:(tem[1]||'')};
  }   
  if(M[1]==='Chrome'){
    tem=ua.match(/\bOPR|Edge\/(\d+)/)
    if(tem!=null)   {return {name:'Opera', version:tem[1]};}
  }   
  M=M[2]? [M[1], M[2]]: [navigator.appName, navigator.appVersion, '-?'];
  if((tem=ua.match(/version\/(\d+)/i))!=null) {M.splice(1,1,tem[1]);}
  return {
    name: M[0],
    version: M[1]
  };
}

/*function getOS() {
  var os = {
    'Windows NT 5.0': 'Windows 2000',
    'Windows NT 5.1': 'Windows XP',
    'Windows NT 6.0': 'Windows Vista',
    'Windows NT 6.1': 'Windows 7',
  }
  alert(os[navigator.userAgent])
}*/

function browserWarn(name) {
    alert('Since you are using an older version of ' + name + ' or an unsupported ' +
          'browser, your game may run slower than expected or not load. Try ' +
          'updating your browser or switching to a different one.');
  }

(function checkUserAgentVersion() {
  var browser = getBrowser();
  if(browser.name === 'Chrome') {
    if(parseInt(browser.version) < 67) { browserWarn(browser.name); }
  }
  if(browser.name === 'Firefox') {
    if(parseInt(browser.version) < 61) { browserWarn(browser.name); }
  }
  if(browser.name === 'Safari') {
    if(parseInt(browser.version) < 12) { browserWarn(browser.name); }
  }
  /*if(browser.name !== 'Firefox') { getOS(); }*/
}());
