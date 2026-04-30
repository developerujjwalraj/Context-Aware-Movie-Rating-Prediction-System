
const API='https://movie-api-kd7m.onrender.com';
let emotion='happy',time='evening',genres=[];
document.querySelectorAll('.e-btn').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.e-btn').forEach(x=>x.classList.remove('on'));b.classList.add('on');emotion=b.dataset.e;}));
document.querySelectorAll('.t-btn').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.t-btn').forEach(x=>x.classList.remove('on'));b.classList.add('on');time=b.dataset.t;}));
document.querySelectorAll('.g-pill').forEach(p=>p.addEventListener('click',()=>{p.classList.toggle('on');const g=p.dataset.g;genres.includes(g)?genres.splice(genres.indexOf(g),1):genres.push(g);}));

let stimer;
document.getElementById('reviewText').addEventListener('input',function(){
  clearTimeout(stimer);
  if(this.value.trim().length<5){document.getElementById('sentBox').classList.remove('show');return;}
  stimer=setTimeout(()=>analyzeSentiment(this.value.trim()),600);
});
async function analyzeSentiment(text){
  try{const r=await fetch(`${API}/api/analyze-sentiment`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});const d=await r.json();showSent(d.sentiment_score,d.sentiment_label,d.detected_emotion);}
  catch{demoSent(text);}
}
function showSent(score,label,det){
  const pct=Math.round((score+1)/2*100);
  document.getElementById('sFill').style.width=pct+'%';
  document.getElementById('sFill').style.background=score>=0?'var(--ink)':'var(--pop)';
  document.getElementById('sLabel').textContent=label.toUpperCase();
  document.getElementById('sEmotion').textContent='→ '+det.toUpperCase()+' detected';
  document.getElementById('sentBox').classList.add('show');
  const btn=document.querySelector(`[data-e="${det}"]`);
  if(btn){document.querySelectorAll('.e-btn').forEach(x=>x.classList.remove('on'));btn.classList.add('on');emotion=det;}
}
function demoSent(text){
  const pw=['good','great','happy','amazing','love','wonderful','fun','excited'];
  const nw=['bad','sad','terrible','hate','awful','boring','stressed','anxious'];
  const words=text.toLowerCase().split(/\s+/);
  const p=words.filter(w=>pw.some(x=>w.includes(x))).length;
  const n=words.filter(w=>nw.some(x=>w.includes(x))).length;
  const score=(p-n)/Math.max(p+n,1);
  const det=score>0.3?'happy':score<-0.3?'sad':'neutral';
  showSent(score,score>0.1?'positive':score<-0.1?'negative':'neutral',det);
}

async function run(){
  const btn=document.getElementById('predictBtn');
  btn.disabled=true;btn.textContent='Analysing…';
  document.getElementById('emptyEl').style.display='none';
  document.getElementById('resultsEl').classList.remove('show');
  document.getElementById('loadingEl').classList.add('show');
  // CHANGED: top_n set to 40
  const payload={emotion,preferred_genres:genres,time_of_day:time,review_text:document.getElementById('reviewText').value,top_n:40};
  try{const r=await fetch(`${API}/api/predict`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});renderResults(await r.json());}
  catch{renderDemo(payload);}
  finally{btn.disabled=false;btn.textContent='Predict Ratings';document.getElementById('loadingEl').classList.remove('show');}
}
function renderResults(data){
  const m=data.metrics;
  document.getElementById('metricsEl').innerHTML=`<div class="metric"><span class="m-val">${m.mae}</span><div class="m-label">MAE</div></div><div class="metric"><span class="m-val">${m.rmse}</span><div class="m-label">RMSE</div></div><div class="metric"><span class="m-val">${m.accuracy}%</span><div class="m-label">Accuracy</div></div>`;
  document.getElementById('ctxBadge').textContent=data.emotion_used.toUpperCase()+' · '+data.time_of_day.toUpperCase();
  const list=document.getElementById('movieListEl');list.innerHTML='';
  data.top_recommendations.forEach((mv,i)=>{
    const pct=Math.round((mv.predicted_rating/5)*100);
    list.innerHTML+=`<div class="movie-row"><div class="m-rank ${i<3?'hi':''}">${String(i+1).padStart(2,'0')}</div><div><div class="m-title">${mv.title}</div><div class="m-sub"><span>${mv.year}</span><span class="m-genre-tag">${mv.genre}</span><span>base ${mv.avg_rating}★</span></div></div><div class="m-score-col"><span class="m-stars">${mv.predicted_rating}</span><div class="m-bar"><div class="m-bar-fill" style="width:${pct}%"></div></div></div></div>`;
  });
  document.getElementById('resultsEl').classList.add('show');
}
// CHANGED: demo fallback expanded to 40 movies
function renderDemo(payload){
  const MV=[
    {title:"Inception",genre:"Sci-Fi",avg_rating:2.3,year:2010},
    {title:"The Dark Knight",genre:"Action",avg_rating:2.7,year:2008},
    {title:"La La Land",genre:"Romance",avg_rating:2.9,year:2016},
    {title:"Interstellar",genre:"Sci-Fi",avg_rating:2.4,year:2014},
    {title:"The Notebook",genre:"Romance",avg_rating:2.7,year:2004},
    {title:"Avengers: Endgame",genre:"Action",avg_rating:2.2,year:2019},
    {title:"Schindler's List",genre:"Drama",avg_rating:2.8,year:1993},
    {title:"The Hangover",genre:"Comedy",avg_rating:2.8,year:2009},
    {title:"Hereditary",genre:"Horror",avg_rating:2.6,year:2018},
    {title:"Parasite",genre:"Thriller",avg_rating:2.5,year:2019},
    {title:"The Grand Budapest Hotel",genre:"Comedy",avg_rating:2.7,year:2014},
    {title:"Mad Max: Fury Road",genre:"Action",avg_rating:2.6,year:2015},
    {title:"Get Out",genre:"Horror",avg_rating:2.7,year:2017},
    {title:"Arrival",genre:"Sci-Fi",avg_rating:2.5,year:2016},
    {title:"Marriage Story",genre:"Drama",avg_rating:2.6,year:2019},
    {title:"Knives Out",genre:"Thriller",avg_rating:2.8,year:2019},
    {title:"Coco",genre:"Animation",avg_rating:2.9,year:2017},
    {title:"The Revenant",genre:"Drama",avg_rating:2.4,year:2015},
    {title:"Crazy Rich Asians",genre:"Romance",avg_rating:2.5,year:2018},
    {title:"John Wick",genre:"Action",avg_rating:2.6,year:2014},
    {title:"1917",genre:"Drama",avg_rating:2.6,year:2019},
    {title:"Once Upon a Time in Hollywood",genre:"Comedy",avg_rating:2.5,year:2019},
    {title:"A Quiet Place",genre:"Horror",avg_rating:2.7,year:2018},
    {title:"The Martian",genre:"Sci-Fi",avg_rating:2.6,year:2015},
    {title:"Bohemian Rhapsody",genre:"Drama",avg_rating:2.7,year:2018},
    {title:"Spider-Man: Into the Spider-Verse",genre:"Animation",avg_rating:2.8,year:2018},
    {title:"Joker",genre:"Thriller",avg_rating:2.5,year:2019},
    {title:"Ford v Ferrari",genre:"Drama",avg_rating:2.7,year:2019},
    {title:"Us",genre:"Horror",avg_rating:2.5,year:2019},
    {title:"The Shape of Water",genre:"Romance",avg_rating:2.6,year:2017},
    {title:"Blade Runner 2049",genre:"Sci-Fi",avg_rating:2.4,year:2017},
    {title:"Dunkirk",genre:"Action",avg_rating:2.5,year:2017},
    {title:"Baby Driver",genre:"Action",avg_rating:2.7,year:2017},
    {title:"Midsommar",genre:"Horror",avg_rating:2.4,year:2019},
    {title:"The Favourite",genre:"Drama",avg_rating:2.5,year:2018},
    {title:"Roma",genre:"Drama",avg_rating:2.6,year:2018},
    {title:"Paddington 2",genre:"Comedy",avg_rating:2.9,year:2017},
    {title:"Three Billboards Outside Ebbing",genre:"Thriller",avg_rating:2.7,year:2017},
    {title:"Call Me by Your Name",genre:"Romance",avg_rating:2.6,year:2017},
    {title:"Whiplash",genre:"Drama",avg_rating:2.8,year:2014}
  ];
  const W={happy:{Comedy:1.5,Romance:1.3,Action:1.2,"Sci-Fi":1.1,Drama:0.9,Horror:0.7,Thriller:0.9,Animation:1.4},sad:{Drama:1.5,Romance:1.4,Comedy:1.2,"Sci-Fi":0.9,Action:0.7,Horror:0.6,Thriller:0.8,Animation:1.1},excited:{Action:1.6,Thriller:1.4,"Sci-Fi":1.3,Comedy:1.1,Horror:1.0,Drama:0.8,Romance:0.9,Animation:1.0},anxious:{Comedy:1.4,Romance:1.2,Drama:1.1,"Sci-Fi":0.9,Action:0.8,Thriller:0.6,Horror:0.5,Animation:1.3},bored:{Action:1.5,Thriller:1.4,"Sci-Fi":1.3,Horror:1.2,Comedy:1.1,Drama:0.9,Romance:0.8,Animation:1.0},stressed:{Comedy:1.5,Romance:1.3,Drama:0.9,Action:0.8,"Sci-Fi":0.9,Thriller:0.6,Horror:0.5,Animation:1.4},romantic:{Romance:1.7,Drama:1.3,Comedy:1.2,"Sci-Fi":0.8,Action:0.7,Thriller:0.9,Horror:0.5,Animation:1.0},neutral:{Drama:1.1,"Sci-Fi":1.1,Comedy:1.0,Action:1.0,Romance:1.0,Thriller:1.0,Horror:0.9,Animation:1.0}};
  const w=W[payload.emotion]||W.neutral;
  const preds=MV.map(m=>{const p=Math.min(5,Math.max(1,m.avg_rating*(w[m.genre]||1)+(payload.preferred_genres.includes(m.genre)?0.3:0)+(Math.random()*0.1-0.05)));return{...m,predicted_rating:Math.round(p*100)/100};}).sort((a,b)=>b.predicted_rating-a.predicted_rating);
  const errs=preds.map(m=>Math.abs(m.predicted_rating-m.avg_rating));
  const mae=(errs.reduce((a,b)=>a+b,0)/errs.length).toFixed(4);
  const rmse=Math.sqrt(errs.map(e=>e*e).reduce((a,b)=>a+b,0)/errs.length).toFixed(4);
  renderResults({emotion_used:payload.emotion,time_of_day:payload.time_of_day,top_recommendations:preds,metrics:{mae,rmse,accuracy:((1-mae/5)*100).toFixed(2)}});
}
const h=new Date().getHours();const auto=h<12?'morning':h<17?'afternoon':h<21?'evening':'night';
document.querySelectorAll('.t-btn').forEach(b=>b.classList.remove('on'));
const ab=document.querySelector(`[data-t="${auto}"]`);if(ab){ab.classList.add('on');time=auto;}
