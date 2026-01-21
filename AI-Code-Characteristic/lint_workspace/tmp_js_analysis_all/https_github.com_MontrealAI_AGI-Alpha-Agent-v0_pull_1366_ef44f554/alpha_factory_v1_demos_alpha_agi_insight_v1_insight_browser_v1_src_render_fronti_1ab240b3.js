// SPDX-License-Identifier: Apache-2.0
import * as Plot from '@observablehq/plot';
import { plotCanvas } from '@observablehq/plot-canvas';
import { paretoFront } from '../utils/pareto.js';
import { credibilityColor } from './colors.js';

export function renderFrontier(container, pop, onSelect) {
  const front = paretoFront(pop).sort((a, b) => a.logic - b.logic);

  const dotOptions = {
    x: 'logic',
    y: 'feasible',
    r: 3,
    fill: (d) => credibilityColor(d.insightCredibility ?? 0),
    title: (d) => `${d.summary ?? ''}\n${d.critic ?? ''}`,
  };

  const marks = [
    Plot.areaY(front, {
      x: 'logic',
      y: 'feasible',
      fill: 'rgba(0,175,255,0.2)',
      stroke: null,
    }),
  ];

  marks.push(
    pop.length > 10000 ? plotCanvas(Plot.dot(pop, dotOptions)) : Plot.dot(pop, dotOptions),
  );

  const plot = Plot.plot({
    width: 500,
    height: 500,
    x: { domain: [0, 1] },
    y: { domain: [0, 1] },
    marks,
  });

  container.innerHTML = '';
  container.append(plot);
  if (onSelect) {
    d3.select(plot).selectAll('circle').on('click', function (_, d) {
      onSelect(d, this);
    });
  }
}
