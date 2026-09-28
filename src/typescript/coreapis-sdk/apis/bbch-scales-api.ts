import { AxiosRequestConfig, AxiosResponse } from 'axios';
import { BaseAPI } from '../base';
import {
    BbchScale,
    BbchScaleCreatePayload,
    BbchScaleDuplicatePayload,
    BbchScaleUpdatePayload,
    FileInfo,
    StatusResponse,
} from '../models';

export class BbchScalesApi extends BaseAPI {
    private options(options?: AxiosRequestConfig): AxiosRequestConfig {
        const baseOptions = this.configuration ? this.configuration.baseOptions : undefined;
        return {
            ...baseOptions,
            ...options,
            headers: {
                ...(baseOptions && baseOptions.headers ? baseOptions.headers : {}),
                ...(options && options.headers ? options.headers : {}),
            },
        };
    }

    public async listBbchScales(options?: AxiosRequestConfig): Promise<AxiosResponse<Array<BbchScale>>> {
        return this.axios.request({ ...this.options(options), method: 'GET', url: `${this.basePath}/v1/bbch-scales` });
    }

    public async getBbchScale(harvestCode: string, options?: AxiosRequestConfig): Promise<AxiosResponse<BbchScale>> {
        return this.axios.request({ ...this.options(options), method: 'GET', url: `${this.basePath}/v1/bbch-scales/${encodeURIComponent(harvestCode)}` });
    }

    public async createBbchScale(body: BbchScaleCreatePayload, options?: AxiosRequestConfig): Promise<AxiosResponse<BbchScale>> {
        return this.axios.request({ ...this.options(options), method: 'POST', url: `${this.basePath}/v1/bbch-scales`, data: body });
    }

    public async updateBbchScale(body: BbchScaleUpdatePayload, harvestCode: string, options?: AxiosRequestConfig): Promise<AxiosResponse<BbchScale>> {
        return this.axios.request({ ...this.options(options), method: 'PUT', url: `${this.basePath}/v1/bbch-scales/${encodeURIComponent(harvestCode)}`, data: body });
    }

    public async duplicateBbchScale(body: BbchScaleDuplicatePayload, sourceHarvestCode: string, options?: AxiosRequestConfig): Promise<AxiosResponse<BbchScale>> {
        return this.axios.request({ ...this.options(options), method: 'POST', url: `${this.basePath}/v1/bbch-scales/${encodeURIComponent(sourceHarvestCode)}/duplicate`, data: body });
    }

    public async deleteBbchScale(harvestCode: string, options?: AxiosRequestConfig): Promise<AxiosResponse<StatusResponse>> {
        return this.axios.request({ ...this.options(options), method: 'DELETE', url: `${this.basePath}/v1/bbch-scales/${encodeURIComponent(harvestCode)}` });
    }

    public async uploadBbchThumbnail(file: Blob, options?: AxiosRequestConfig): Promise<AxiosResponse<FileInfo>> {
        const data = new FormData();
        data.append('file', file);
        return this.axios.request({ ...this.options(options), method: 'POST', url: `${this.basePath}/v1/bbch-scales/thumbnails/upload`, data });
    }
}
