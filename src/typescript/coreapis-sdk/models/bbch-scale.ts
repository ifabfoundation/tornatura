import { BbchGroup } from './bbch-group';

export interface BbchScale {
    id: string;
    harvestCode: string;
    sourceHarvestCode?: string | null;
    groups?: Array<BbchGroup>;
    creationTime: number;
    lastUpdateTime: number;
}
