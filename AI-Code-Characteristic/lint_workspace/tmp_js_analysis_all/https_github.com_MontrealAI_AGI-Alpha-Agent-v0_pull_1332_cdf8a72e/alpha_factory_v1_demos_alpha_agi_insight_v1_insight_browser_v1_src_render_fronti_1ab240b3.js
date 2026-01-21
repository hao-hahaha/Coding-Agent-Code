// SPDX-License-Identifier: Apache-2.0
import * as d3 from 'd3';
import { showTooltip, hideTooltip } from '../ui/Tooltip.js';
import { paretoFront } from '../utils/pareto.js';
import { strategyColors } from './colors.js';
import { drawPoints } from './canvasLayer.js';

export function addGlow(svg) {
  const defs = svg.append('defs');
  const filter = defs.append('filter').attr('id', 'glow');
  filter.append('feGaussianBlur').attr('stdDeviation', 2).attr('result', 'blur');
  const merge = filter.append('feMerge');
  merge.append('feMergeNode').attr('in', 'blur');
  merge.append('feMergeNode').attr('in', 'SourceGraphic');
}

export function renderFrontier(svg, pop, x, y) {
  const front = paretoFront(pop).sort((a, b) => a.logic - b.logic);

  const area = d3
    .area()
    .x((d) => x(d.logic))
    .y0(y.range()[0])
    .y1((d) => y(d.feasible));

  let g = svg.select('g#frontier');
  if (g.empty()) g = svg.append('g').attr('id', 'frontier');

  g.selectAll('path')
    .data([front])
    .join('path')
    .attr('fill', 'rgba(0,175,255,0.2)')
    .attr('stroke', 'none')
    .attr('d', area);

  let dots = svg.select('g#dots');
  if (dots.empty()) dots = svg.append('g').attr('id', 'dots');

  if (pop.length > 5000) {
    dots.selectAll('circle').remove();
    const frontSet = new Set(front);
    drawPoints(dots, pop, x, y, (d) => {
      if (frontSet.has(d)) return strategyColors.front;
      return strategyColors[d.strategy] || strategyColors.base;
    });
  } else {
    const node = dots.node();
    const fo = node.querySelector('foreignObject#canvas-layer');
    if (fo) fo.remove();

    dots
      .selectAll('circle')
      .data(pop)
      .join('circle')
      .attr('cx', (d) => x(d.logic))
      .attr('cy', (d) => y(d.feasible))
      .attr('r', 3)
      .attr('fill', (d) => {
        if (front.includes(d)) return strategyColors.front;
        return strategyColors[d.strategy] || strategyColors.base;
      })
      .attr('filter', (d) => (front.includes(d) ? 'url(#glow)' : null))
      .on('mousemove', (ev, d) =>
        showTooltip(
          ev.pageX + 6,
          ev.pageY + 6,
          `logic: ${d.logic.toFixed(2)}\nfeas: ${d.feasible.toFixed(2)}`
        )
      )
      .on('mouseleave', hideTooltip);
  }
}
