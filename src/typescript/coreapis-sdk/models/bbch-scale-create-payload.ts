import { BbchGroup } from './bbch-group';

export interface BbchScaleCreatePayload {
    harvestCode: string;
    sourceHarvestCode?: string | null;
    groups?: Array<BbchGroup>;
}
