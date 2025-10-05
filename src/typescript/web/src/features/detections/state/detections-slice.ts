
import {
  createSlice,
  createAsyncThunk,
  createEntityAdapter,
  createSelector,
} from "@reduxjs/toolkit";
import { Detection, DetectionMutationPayload, DetectionsApi } from "@tornatura/coreapis";
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
  async ({orgId, fieldId, page=1, limit=1000}: IFetchFieldDetections, ) => {
    const apiConfig = await getCoreApiConfiguration();
    const detectionsApi = new DetectionsApi(apiConfig);
    const data = detectionsApi.listDetections(orgId, fieldId, page, limit).then((response) => {
      return response.data;
    });
    return data;
  }
);

interface IAddNewDetectionPayload {
  orgId: string;
  fieldId: string;
  body: DetectionMutationPayload
}

export const addNewDetection = createAsyncThunk(
  "detections/addNewDetection",
  async ({orgId, fieldId, body}: IAddNewDetectionPayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration()
    const apiInstance = new DetectionsApi(apiConfig);
    try {
      const response = await apiInstance.createDetection(body, orgId, fieldId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);


interface IUpdateDetectionPayload {
  orgId: string;
  fieldId: string;
  detectionId: string;
  body: DetectionMutationPayload
}

export const updateDetection = createAsyncThunk(
  "detections/updateDetection",
  async ({orgId, fieldId, detectionId, body}: IUpdateDetectionPayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration()
    const apiInstance = new DetectionsApi(apiConfig);
    try {
      const response = await apiInstance.updateDetection(body, orgId, fieldId, detectionId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

const detectionsSlice = createSlice({
  name: "detections",
  initialState,
  reducers: {
  },
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

    builder.addCase(addNewDetection.fulfilled, (state, action) => {
      detectionsAdapter.upsertOne(state, action.payload as Detection);
    });

    builder.addCase(updateDetection.fulfilled, (state, action) => {
      detectionsAdapter.upsertOne(state, action.payload as Detection);
    });
  },
});

const selectors = detectionsAdapter.getSelectors<RootState>(
  (state) => state.detections
);

export const detectionsSelectors = {
  selectDetections: selectors.selectAll,
  selectDetectionbyFieldId: createSelector(
    [
      selectors.selectAll,
      (_, fieldId) => fieldId
    ],
    (detections, fieldId) => detections.filter((item: Detection) => item.agrifieldId === fieldId)
  ),
  selectDetectionbyOrgId: createSelector(
    [
      selectors.selectAll,
      (state, orgId) => fieldsSelectors.selectFieldsByOrgId(state, orgId)
    ],
    (detections, fields) => detections.filter((item: Detection) => fields.map(f => f.id).includes(item.agrifieldId))
  )
};

export const detectionsActions = {
  fetchFieldDetectionsAction: fetchFieldDetections,
  addNewDetectionAction: addNewDetection,
  updateDetectionAction: updateDetection,
};


export const detectionsReducer = detectionsSlice.reducer;
