import { BbchStage } from './bbch-stage';

export interface BbchGroup {
    code: string;
    name: string;
    icon?: string | null;
    sortOrder?: number;
    stages?: Array<BbchStage>;
}
