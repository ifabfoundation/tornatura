import {
  createSlice,
  createAsyncThunk,
  createEntityAdapter,
  createSelector,
} from "@reduxjs/toolkit";
import {
  DetectionType,
  DetectionTypeCreatePayload,
  DetectionTypeUpdatePayload,
  DetectionTypesApi,
} from "@tornatura/coreapis";
import { getCoreApiConfiguration } from "../../../services/utils";
import { AuxState } from "../../../hooks";
import { RootState } from "../../../store";


const detectionTypesAdapter = createEntityAdapter<DetectionType, string>({
  selectId: (detectionType: DetectionType) => detectionType.id,
});

const initialState = detectionTypesAdapter.getInitialState<AuxState>({
  status: "idle",
  total: 0,
  error: undefined,
  currentRequestId: "",
});

interface IFetchDetectionTypes {
  orgId: string;
  fieldId: string;
  page?: number;
  limit?: number;
}

export const fetchDetectionTypes = createAsyncThunk(
  "detectionTypes/fetchDetectionTypes",
  async ({ orgId, fieldId, page = 1, limit = 1000 }: IFetchDetectionTypes) => {
    const apiConfig = await getCoreApiConfiguration();
    const detectionTypesApi = new DetectionTypesApi(apiConfig);
    const data = detectionTypesApi
      .listDetectionTypes(orgId, fieldId, page, limit)
      .then((response) => response.data);
    return data;
  }
);

interface IAddDetectionTypePayload {
  orgId: string;
  fieldId: string;
  body: DetectionTypeCreatePayload;
}

export const addDetectionType = createAsyncThunk(
  "detectionTypes/addDetectionType",
  async ({ orgId, fieldId, body }: IAddDetectionTypePayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const detectionTypesApi = new DetectionTypesApi(apiConfig);
    try {
      const response = await detectionTypesApi.createDetectionType(body, orgId, fieldId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

interface IUpdateDetectionTypePayload {
  orgId: string;
  fieldId: string;
  detectionTypeId: string;
  body: DetectionTypeUpdatePayload;
}

export const updateDetectionType = createAsyncThunk(
  "detectionTypes/updateDetectionType",
  async (
    { orgId, fieldId, detectionTypeId, body }: IUpdateDetectionTypePayload,
    { rejectWithValue }
  ) => {
    const apiConfig = await getCoreApiConfiguration();
    const detectionTypesApi = new DetectionTypesApi(apiConfig);
    try {
      const response = await detectionTypesApi.updateDetectionType(body, orgId, fieldId, detectionTypeId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

interface IDeleteDetectionTypePayload {
  orgId: string;
  fieldId: string;
  detectionTypeId: string;
}

export const deleteDetectionType = createAsyncThunk(
  "detectionTypes/deleteDetectionType",
  async ({ orgId, fieldId, detectionTypeId }: IDeleteDetectionTypePayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const detectionTypesApi = new DetectionTypesApi(apiConfig);
    try {
      await detectionTypesApi.deleteDetectionType(orgId, fieldId, detectionTypeId);
      return detectionTypeId;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

const detectionTypesSlice = createSlice({
  name: "detectionTypes",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(fetchDetectionTypes.pending, (state) => {
      state.status = "pending";
    });

    builder.addCase(fetchDetectionTypes.fulfilled, (state, action) => {
      state.status = "succeeded";
      state.total = action.payload.total;
      detectionTypesAdapter.setAll(state, action.payload.data as DetectionType[]);
    });

    builder.addCase(fetchDetectionTypes.rejected, (state, action) => {
      state.status = "failed";
      state.error = action.error.message;
    });

    builder.addCase(addDetectionType.fulfilled, (state, action) => {
      detectionTypesAdapter.upsertOne(state, action.payload as DetectionType);
    });

    builder.addCase(updateDetectionType.fulfilled, (state, action) => {
      detectionTypesAdapter.upsertOne(state, action.payload as DetectionType);
    });

    builder.addCase(deleteDetectionType.fulfilled, (state, action) => {
      detectionTypesAdapter.removeOne(state, action.payload as string);
    });
  },
});

const selectors = detectionTypesAdapter.getSelectors<RootState>(
  (state) => state.detectionTypes
);

export const detectionTypesSelectors = {
  selectDetectionTypes: selectors.selectAll,
  selectDetectionTypeById: selectors.selectById,
  selectDetectionTypesByField: createSelector(
    [selectors.selectAll, (_: RootState, fieldId: string) => fieldId],
    (types, fieldId) => types.filter((item) => item.agrifieldId === fieldId)
  ),
};

export const detectionTypesActions = {
  fetchDetectionTypesAction: fetchDetectionTypes,
  addDetectionTypeAction: addDetectionType,
  updateDetectionTypeAction: updateDetectionType,
  deleteDetectionTypeAction: deleteDetectionType,
};

export const detectionTypesReducer = detectionTypesSlice.reducer;
