import {
  createSlice,
  createAsyncThunk,
  createEntityAdapter,
  createSelector,
} from "@reduxjs/toolkit";
import {
  Detection,
  DetectionMutationPayload,
  DetectionsApi,
  MultiDetectionCreateResponse,
  MultiDetectionMutationPayload,
} from "@tornatura/coreapis";
import { getCoreApiConfiguration } from "../../../services/utils";
import { AuxState } from "../../../hooks";
import { RootState } from "../../../store";
import { fieldsSelectors } from "../../fields/state/fields-slice";

const detectionsAdapter = createEntityAdapter<Detection, string>({
  selectId: (detection: Detection) => detection.id,
});

const initialState = detectionsAdapter.getInitialState<AuxState>({
  status: "idle",
  total: 0,
  error: undefined,
  currentRequestId: "",
});

interface IFetchFieldDetections {
  orgId: string;
  fieldId: string;
  page?: number;
  limit?: number;
}

export const fetchFieldDetections = createAsyncThunk(
  "detections/fetchFieldDetections",
  async ({ orgId, fieldId, page = 1, limit = 1000 }: IFetchFieldDetections) => {
    const apiConfig = await getCoreApiConfiguration();
    const detectionsApi = new DetectionsApi(apiConfig);
    const data = detectionsApi
      .listDetections(orgId, fieldId, undefined, page, limit)
      .then((response) => {
        return response.data;
      });
    return data;
  },
);

interface IFetchDetectionsByType {
  orgId: string;
  fieldId: string;
  detectionTypeId: string;
  page?: number;
  limit?: number;
}

export const fetchDetectionsByType = createAsyncThunk(
  "detections/fetchDetectionsByType",
  async ({ orgId, fieldId, detectionTypeId, page = 1, limit = 1000 }: IFetchDetectionsByType) => {
    const apiConfig = await getCoreApiConfiguration();
    const detectionsApi = new DetectionsApi(apiConfig);
    const data = detectionsApi
      .listDetections(orgId, fieldId, detectionTypeId, page, limit)
      .then((response) => response.data);
    return data;
  },
);

interface IAddNewDetectionPayload {
  orgId: string;
  fieldId: string;
  body: DetectionMutationPayload;
}

interface IAddBulkDetectionsPayload {
  orgId: string;
  fieldId: string;
  body: MultiDetectionMutationPayload;
}

export const addNewDetection = createAsyncThunk(
  "detections/addNewDetection",
  async ({ orgId, fieldId, body }: IAddNewDetectionPayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const apiInstance = new DetectionsApi(apiConfig);
    try {
      const response = await apiInstance.createDetection(body, orgId, fieldId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  },
);

export const addBulkDetections = createAsyncThunk(
  "detections/addBulkDetections",
  async ({ orgId, fieldId, body }: IAddBulkDetectionsPayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const apiInstance = new DetectionsApi(apiConfig);
    try {
      const response = await apiInstance.createBulkDetections(body, orgId, fieldId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  },
);

interface IDeleteDetectionPayload {
  orgId: string;
  fieldId: string;
  detectionId: string;
}

export const deleteDetection = createAsyncThunk(
  "detections/deleteDetection",
  async ({ orgId, fieldId, detectionId }: IDeleteDetectionPayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const apiInstance = new DetectionsApi(apiConfig);
    try {
      await apiInstance.deleteDetection(orgId, fieldId, detectionId);
      return detectionId;
    } catch (error) {
      return rejectWithValue(error);
    }
  },
);

interface IUpdateDetectionTimePayload {
  orgId: string;
  fieldId: string;
  detectionId: string;
  detectionTime: number;
}

/**
 * Corregge il momento in cui un rilevamento e' stato fatto.
 *
 * Passa da `fetch` e non dall'SDK: la rotta esiste nel core ma non nel pacchetto
 * `@tornatura/coreapis`, che la web consuma come tarball pre-compilato. E' lo stesso
 * approccio gia' usato per `/v1/forms/.../pdf` in `pages/auth.tsx`. L'indirizzo e il
 * token (con rinnovo) arrivano comunque da `getCoreApiConfiguration`, per non
 * duplicare la logica di autenticazione.
 *
 * Se il rilevamento fa parte di una sessione multipla il server sposta TUTTI i suoi
 * membri, perche' condividono un solo `detectionTime`, e li restituisce: per questo la
 * risposta e' una lista e il reducer fa `upsertMany`.
 */
export const updateDetectionTime = createAsyncThunk(
  "detections/updateDetectionTime",
  async (
    { orgId, fieldId, detectionId, detectionTime }: IUpdateDetectionTimePayload,
    { rejectWithValue },
  ) => {
    const apiConfig = await getCoreApiConfiguration();
    try {
      const response = await fetch(
        `${apiConfig.basePath}/v1/organizations/${orgId}/agrifields/${fieldId}/detections/${detectionId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            ...((apiConfig.baseOptions?.headers ?? {}) as Record<string, string>),
          },
          body: JSON.stringify({ detectionTime }),
        },
      );
      if (!response.ok) {
        return rejectWithValue(await response.text());
      }
      const data = (await response.json()) as {
        sessionId: string | null;
        detections: Detection[];
      };
      return data.detections;
    } catch (error) {
      return rejectWithValue(error);
    }
  },
);

const detectionsSlice = createSlice({
  name: "detections",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(fetchFieldDetections.pending, (state) => {
      state.status = "pending";
    });

    builder.addCase(fetchFieldDetections.fulfilled, (state, action) => {
      state.status = "succeeded";
      state.total = action.payload.total;
      detectionsAdapter.upsertMany(state, action.payload.data as Detection[]);
    });

    builder.addCase(fetchFieldDetections.rejected, (state, action) => {
      state.status = "failed";
      state.error = action.error.message;
    });

    builder.addCase(fetchDetectionsByType.pending, (state) => {
      state.status = "pending";
    });

    builder.addCase(fetchDetectionsByType.fulfilled, (state, action) => {
      state.status = "succeeded";
      state.total = action.payload.total;
      detectionsAdapter.upsertMany(state, action.payload.data as Detection[]);
    });

    builder.addCase(fetchDetectionsByType.rejected, (state, action) => {
      state.status = "failed";
      state.error = action.error.message;
    });

    builder.addCase(addNewDetection.fulfilled, (state, action) => {
      detectionsAdapter.upsertOne(state, action.payload as Detection);
    });

    builder.addCase(addBulkDetections.fulfilled, (state, action) => {
      detectionsAdapter.upsertMany(
        state,
        (action.payload as MultiDetectionCreateResponse).detections as Detection[],
      );
    });

    builder.addCase(deleteDetection.fulfilled, (state, action) => {
      detectionsAdapter.removeOne(state, action.payload as string);
    });

    builder.addCase(updateDetectionTime.fulfilled, (state, action) => {
      detectionsAdapter.upsertMany(state, action.payload as Detection[]);
    });
  },
});

const selectors = detectionsAdapter.getSelectors<RootState>((state) => state.detections);

export const detectionsSelectors = {
  selectDetections: selectors.selectAll,
  selectDetectionById: selectors.selectById,
  selectDetectionbyFieldId: createSelector(
    [selectors.selectAll, (_, fieldId) => fieldId],
    (detections, fieldId) => detections.filter((item: Detection) => item.agrifieldId === fieldId),
  ),
  selectDetectionbyOrgId: createSelector(
    [selectors.selectAll, (state, orgId) => fieldsSelectors.selectFieldsByOrgId(state, orgId)],
    (detections, fields) =>
      detections.filter((item: Detection) => fields.map((f) => f.id).includes(item.agrifieldId)),
  ),
  selectDetectionByTypeId: createSelector(
    [selectors.selectAll, (_, detectionTypeId) => detectionTypeId],
    (detections, detectionTypeId) =>
      detections.filter((item: Detection) => item.detectionTypeId === detectionTypeId),
  ),
};

export const detectionsActions = {
  fetchFieldDetectionsAction: fetchFieldDetections,
  fetchDetectionsByTypeAction: fetchDetectionsByType,
  addNewDetectionAction: addNewDetection,
  addBulkDetectionsAction: addBulkDetections,
  deleteDetectionAction: deleteDetection,
  updateDetectionTimeAction: updateDetectionTime,
};

export const detectionsReducer = detectionsSlice.reducer;
