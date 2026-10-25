import { mountAcademy, parseLevelHash, type LevelId } from './index';

const root = document.querySelector('#app');
if (!root) throw new Error('missing #app');

function current(): LevelId {
  return parseLevelHash(location.hash) ?? 'L1';
}

const handle = mountAcademy(root as HTMLElement, { levelId: current() });
window.addEventListener('hashchange', () => handle.navigate(current()));
