const $ = (id) => document.getElementById(id);

async function loadMeta() {
  try {
    const r = await fetch('/meta');
    const m = await r.json();
    $('meta').textContent =
      `${m.car_count} model-years across ${m.model_count} models, ` +
      `${m.years[0]}–${m.years[m.years.length - 1]}. Source: ${m.source}`;
  } catch {
    $('meta').textContent = 'Could not load dataset info.';
  }
}

function bar(label, value) {
  return `
    <div class="bar-row">
      <span>${label}</span>
      <span class="bar-track"><span class="bar-fill" style="width:${value}%"></span></span>
      <span>${value}</span>
    </div>`;
}

function card(c, index) {
  const caveats = c.caveats
    .map((t) => `<div class="caveat">${t}</div>`)
    .join('');

  return `
    <article class="result">
      <h3>${index + 1}. ${c.year} ${c.make} ${c.model}</h3>
      <div class="rank">
        <div class="score">${c.fit}</div>
        <div class="score-label">fit</div>
      </div>
      <div class="body-line">${c.body} · seats ${c.seats}</div>
      <div class="bars">
        ${bar('Reliability', c.reliability)}
        ${bar('Safety', c.safety)}
      </div>
      <div class="why">${c.why}</div>
      ${caveats}
    </article>`;
}

async function find() {
  const btn = $('findBtn');
  btn.disabled = true;
  btn.textContent = 'Looking…';
  $('notes').innerHTML = '';
  $('results').innerHTML = '';

  const minYear = $('minYear').value;
  const payload = {
    kids: Number($('kids').value),
    priority: $('priority').value,
    min_year: minYear ? Number(minYear) : null,
  };

  try {
    const r = await fetch('/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!r.ok) throw new Error(`server returned ${r.status}`);
    const data = await r.json();

    $('notes').innerHTML = data.notes
      .map((n) => `<div class="note">${n}</div>`)
      .join('');

    $('results').innerHTML = data.results.length
      ? data.results.map(card).join('')
      : '<p class="empty">No cars in the dataset match that.</p>';
  } catch (err) {
    $('results').innerHTML =
      `<p class="empty">Something went wrong: ${err.message}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Find my car';
  }
}

$('findBtn').addEventListener('click', find);
loadMeta();
find();
