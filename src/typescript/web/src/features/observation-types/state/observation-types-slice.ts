import {
  createSlice,
  createAsyncThunk,
  createEntityAdapter,
  createSelector,
} from "@reduxjs/toolkit";
import {
  ObservationType,
  ObservationTypeCreatePayload,
  ObservationTypeUpdatePayload,
  ObservationTypesApi,
} from "@tornatura/coreapis";
import { getCoreApiConfiguration } from "../../../services/utils";
import { AuxState } from "../../../hooks";
import { RootState } from "../../../store";


const observationTypesAdapter = createEntityAdapter<ObservationType, string>({
  selectId: (observationType: ObservationType) => observationType.id,
});

const initialState = observationTypesAdapter.getInitialState<AuxState>({
  status: "idle",
  total: 0,
  error: undefined,
  currentRequestId: "",
});

interface IFetchObservationTypes {
  page?: number;
  limit?: number;
}

export const fetchObservationTypes = createAsyncThunk(
  "observationTypes/fetchObservationTypes",
  async ({ page = 1, limit = 1000 }: IFetchObservationTypes) => {
    const apiConfig = await getCoreApiConfiguration();
    const observationTypesApi = new ObservationTypesApi(apiConfig);
    const data = observationTypesApi
      .listObservationTypes(page, limit)
      .then((response) => response.data);
    return data;
  }
);

export const addObservationType = createAsyncThunk(
  "observationTypes/addObservationType",
  async (body: ObservationTypeCreatePayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const observationTypesApi = new ObservationTypesApi(apiConfig);
    try {
      const response = await observationTypesApi.createObservationType(body);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

interface IUpdateObservationTypePayload {
  observationTypeId: string;
  body: ObservationTypeUpdatePayload;
}

export const updateObservationType = createAsyncThunk(
  "observationTypes/updateObservationType",
  async ({ observationTypeId, body }: IUpdateObservationTypePayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const observationTypesApi = new ObservationTypesApi(apiConfig);
    try {
      const response = await observationTypesApi.updateObservationType(body, observationTypeId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const deleteObservationType = createAsyncThunk(
  "observationTypes/deleteObservationType",
  async (observationTypeId: string, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const observationTypesApi = new ObservationTypesApi(apiConfig);
    try {
      await observationTypesApi.deleteObservationType(observationTypeId);
      return observationTypeId;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

const observationTypesSlice = createSlice({
  name: "observationTypes",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(fetchObservationTypes.pending, (state) => {
      state.status = "pending";
    });

    builder.addCase(fetchObservationTypes.fulfilled, (state, action) => {
      state.status = "succeeded";
      state.total = action.payload.total;
      observationTypesAdapter.setAll(state, action.payload.data as ObservationType[]);
    });

    builder.addCase(fetchObservationTypes.rejected, (state, action) => {
      state.status = "failed";
      state.error = action.error.message;
    });

    builder.addCase(addObservationType.fulfilled, (state, action) => {
      observationTypesAdapter.upsertOne(state, action.payload as ObservationType);
    });

    builder.addCase(updateObservationType.fulfilled, (state, action) => {
      observationTypesAdapter.upsertOne(state, action.payload as ObservationType);
    });

    builder.addCase(deleteObservationType.fulfilled, (state, action) => {
      observationTypesAdapter.removeOne(state, action.payload as string);
    });
  },
});

const selectors = observationTypesAdapter.getSelectors<RootState>(
  (state) => state.observationTypes
);

export const observationTypesSelectors = {
  selectObservationTypes: selectors.selectAll,
  selectObservationTypeById: selectors.selectById,
  selectObservationTypesByTypologyAndMethod: createSelector(
    [
      selectors.selectAll,
      (_: RootState, typology: string) => typology,
      (_: RootState, _typology: string, method: string) => method,
    ],
    (types, typology, method) =>
      types.filter((item) => item.typology === typology && item.method === method)
  ),
};

export const observationTypesActions = {
  fetchObservationTypesAction: fetchObservationTypes,
  addObservationTypeAction: addObservationType,
  updateObservationTypeAction: updateObservationType,
  deleteObservationTypeAction: deleteObservationType,
};

export const observationTypesReducer = observationTypesSlice.reducer;
