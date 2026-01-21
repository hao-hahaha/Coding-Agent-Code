
async function refresh(){
  const tbody=document.querySelector('#tbl tbody');
  try{
    const res=await fetch('/api/logs?limit=50');
    if(!res.ok) throw new Error('HTTP '+res.status);
    const data=await res.json();
    if(!data.length){
      tbody.innerHTML='<tr><td colspan="4" class="empty">No logs yet</td></tr>';
      return;
    }
    tbody.innerHTML='';
    data.forEach(r=>{
      const tr=document.createElement('tr');
      tr.innerHTML=`<td>${r.ts}</td><td>${r.agent}</td><td>${r.kind}</td><td><pre>${JSON.stringify(r.data,null,2)}</pre></td>`;
      tbody.appendChild(tr);
    });
  }catch(err){
    tbody.innerHTML=`<tr><td colspan="4" class="error">Error loading logs: ${err}</td></tr>`;
  }
}
setInterval(refresh,5000);refresh();
