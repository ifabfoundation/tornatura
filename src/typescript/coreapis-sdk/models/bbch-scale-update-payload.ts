import { BbchGroup } from './bbch-group';

export interface BbchScaleUpdatePayload {
    sourceHarvestCode?: string | null;
    groups?: Array<BbchGroup> | null;
}
