(function(){
  const {useState, useEffect} = React;
  function App(){
    const [data, setData] = useState([]);
    useEffect(()=>{
      fetch('/results')
        .then(r => r.ok ? r.json() : {forecast: []})
        .then(d => setData(d.forecast || []))
        .catch(()=>{});
    },[]);
    useEffect(()=>{
      if(data.length){
        Plotly.react('timeline',[{
          x: data.map(p=>p.year),
          y: data.map(p=>p.capability),
          mode:'lines+markers',
          type:'scatter'
        }],{});
      }
    },[data]);
    return React.createElement('div',null,
      React.createElement('h1',null,'Disruption Timeline'),
      React.createElement('div',{id:'timeline',style:{width:'100%',height:300}})
    );
  }
  const root = ReactDOM.createRoot(document.getElementById('root'));
  root.render(React.createElement(App));
})();
