import { TaskLabelInput } from '../models';

export function formatTaskLabel(task: TaskLabelInput | null | undefined): string {
  if (!task) {
    return 'SIN-DATOS';
  }
  const priority = task.priority ? String(task.priority).toUpperCase() : 'NORMAL';
  const owner = task.owner ? String(task.owner).toUpperCase() : 'SIN-ASIGNAR';
  return priority + ' · ' + owner;
}
