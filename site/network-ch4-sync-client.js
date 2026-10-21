/* Static-site notice: local progress remains unchanged; Google login and Drive sync are not connected. */
(()=>{'use strict';if(window.CoursePreview)return;if(!window.CourseReading)return;
const message='Google Drive 同步待接通 · 本机保存状态见阅读面板';
window.CourseDriveStatusText=message;
const panel=document.createElement('section');panel.className='rp-drive';
const heading=document.createElement('h3');heading.textContent='保存与同步';
const state=document.createElement('p');state.className='rp-drive-status';state.textContent=message;
const note=document.createElement('p');note.textContent='此静态站尚未接通 Google 登录与 Drive 同步。仅提供本机保存，是否成功以阅读面板状态为准；请使用下方 JSON 导出和导入备份。旧站及旧 Drive 记录不会被此站修改，原网址的本机记录也不会自动迁入。';
panel.append(heading,state,note);document.querySelector('.rp-backup')?.before(panel);
})();
