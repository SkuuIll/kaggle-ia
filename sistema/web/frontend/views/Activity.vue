<template>
  <section data-view="actividad" hidden>
    <article id="current-operation" class="panel activity-operation">
      <div class="panel-title">
        <h2>
          <i id="job-pulse" class="pulse" hidden></i> <span id="jobtitle">Sin operaciones en curso</span>
        </h2>
        <span id="job-duration" class="small muted"></span>
      </div>
      <p id="job-note" class="hint" role="status">El inicio y el apagado se confirman contra Kaggle.</p>
      <p id="job-updated" class="hint"></p>
      <ol id="job-stages" class="job-stages" aria-label="Etapas de la operación" hidden></ol>
      <details class="operation-log">
        <summary>Registro técnico</summary>
        <pre id="progress" class="log" aria-label="Registro de la operación">
Todavía no hay una operación en esta sesión del servidor.</pre>
        <p id="runtime-stage" class="notice" role="status"></p>
      </details>
      <div id="job-download"></div>
    </article>
    <article class="panel">
      <div class="panel-title">
        <div>
          <h2>Historial de operaciones</h2>
          <p>Se conserva al cerrar el navegador o reiniciar el panel.</p>
        </div>
        <label class="sr-only" for="history-filter">Filtrar historial</label
        ><select id="history-filter" class="filter" onchange="renderHistory()">
          <option value="all">Todos los resultados</option>
          <option value="done">Completadas</option>
          <option value="error">Con errores</option>
        </select>
      </div>
      <div id="operation-history"></div>
    </article>
  </section>
</template>
