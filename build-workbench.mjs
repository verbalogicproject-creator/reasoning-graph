import {copyFileSync} from 'node:fs';
const target = 'reasoning_graph/workbench/static/';
copyFileSync('node_modules/@primer/css/dist/core.css', target + 'primer.css');
copyFileSync('node_modules/cytoscape/dist/cytoscape.min.js', target + 'cytoscape.min.js');
