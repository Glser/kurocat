// Satin ivory case and front-printed caps, sampled by physical row (not screen row).
export const keyboardCase = { rim: '#f0e5d2', edge: '#c3b297', bed: '#dfd1ba' };
export const keyRows = [
  { top: '#f4ecdc', side: '#c6bba5' },
  { top: '#d0e0e6', side: '#98adba' },
  { top: '#bfd8e6', side: '#86a8bd' },
  { top: '#accde2', side: '#729ab6' },
  { top: '#92bedf', side: '#608bad' },
  { top: '#86b3d8', side: '#5b829f' },
];
const print: Record<string, string> = {
  space: '―', bs: '←', tab: 'Tab', caps: 'Caps', enter: 'Enter', np_ent: 'Enter',
  lshift: '⇧ Shift', rshift: '⇧ Shift', prt: 'Print', del: 'Delete', home: 'Home',
  ins: 'Insert', pgup: 'PgUp', pgdn: 'PgDn',
};
export const frontLegend = (key: { id: string; label: string }) => print[key.id] ?? key.label;
