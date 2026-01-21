(function(){
  const {useState, useEffect} = React;
  function App(){
    const [data, setData] = useState([]);
    const [pop, setPop] = useState([]);
    useEffect(()=>{
      fetch('/results')
        .then(r => r.ok ? r.json() : {forecast: [], population: []})
        .then(d => { setData(d.forecast || []); setPop(d.population || []); })
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
    useEffect(()=>{
      if(pop.length){
        Plotly.react('population',[{
          x: pop.map(p=>p.effectiveness),
          y: pop.map(p=>p.risk),
          z: pop.map(p=>p.complexity),
          mode:'markers',
          type:'scatter3d',
          marker:{color: pop.map(p=>p.rank)}
        }],{scene:{xaxis:{title:'Effectiveness'},yaxis:{title:'Risk'},zaxis:{title:'Complexity'}}});
      }
    },[pop]);
    return React.createElement('div',null,
      React.createElement('h1',null,'Disruption Timeline'),
      React.createElement('div',{id:'timeline',style:{width:'100%',height:300}}),
      React.createElement('div',{id:'population',style:{width:'100%',height:400}})
    );
  }
  const root = ReactDOM.createRoot(document.getElementById('root'));
  root.render(React.createElement(App));
})();
