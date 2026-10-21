/* Copy-only, user-triggered actions. No navigation, message API or learning state. */
(()=>{'use strict';
async function act({text,clipboard}){
 try{if(!clipboard?.writeText)throw Error('Clipboard unavailable');await clipboard.writeText(text);return {copied:true};}catch{return {copied:false};}
}
window.CourseAskCore={act};
})();
