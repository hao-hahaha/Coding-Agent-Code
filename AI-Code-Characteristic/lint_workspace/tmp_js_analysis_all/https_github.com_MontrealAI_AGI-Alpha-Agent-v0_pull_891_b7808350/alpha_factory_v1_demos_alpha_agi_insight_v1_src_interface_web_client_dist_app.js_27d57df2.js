(function(){
  const {useState, useEffect} = React;
  const API_TOKEN = 'demo-token';
  function App(){
    const [horizon,setHorizon]=useState(5);
    const [pop,setPop]=useState(6);
    const [gen,setGen]=useState(3);
    const [runId,setRunId]=useState(null);
    const [years,setYears]=useState([]);
    const [caps,setCaps]=useState([]);
    async function start(e){
      e.preventDefault();
      const res=await fetch('/simulate',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+API_TOKEN},body:JSON.stringify({horizon, pop_size:pop, generations:gen})});
      const d=await res.json();
      setRunId(d.id);setYears([]);setCaps([]);
    }
    useEffect(()=>{
      if(!runId)return;
      const ws=new WebSocket('ws://'+location.host+'/ws/progress');
      ws.onopen=()=>ws.send('ready');
      ws.onmessage=ev=>{try{const m=JSON.parse(ev.data);if(m.id===runId){setYears(y=>y.concat(m.year));setCaps(c=>c.concat(m.capability));}}catch{}}
      return ()=>ws.close();
    },[runId]);
    useEffect(()=>{if(years.length){Plotly.react('chart',[{x:years,y:caps,mode:'lines+markers',type:'scatter'}],{margin:{t:20}});}},[years,caps]);
    return React.createElement('div',null,
      React.createElement('h2',null,'\u03B1\u2011AGI Insight'),
      React.createElement('form',{onSubmit:start,style:{marginBottom:'1em'}},
        React.createElement('label',null,'Horizon',React.createElement('input',{type:'number',value:horizon,onChange:e=>setHorizon(+e.target.value)})),
        React.createElement('label',null,' Population',React.createElement('input',{type:'number',value:pop,onChange:e=>setPop(+e.target.value)})),
        React.createElement('label',null,' Generations',React.createElement('input',{type:'number',value:gen,onChange:e=>setGen(+e.target.value)})),
        React.createElement('button',{type:'submit'},'Run')
      ),
      React.createElement('div',{id:'chart',style:{width:'100%',height:400}})
    );
  }
  ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(App));
})();
