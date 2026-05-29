import {
  createSlice,
  createAsyncThunk,
  createEntityAdapter,
  createSelector,
} from "@reduxjs/toolkit";
import {
  HarvestType,
  HarvestTypeCreatePayload,
  HarvestTypeUpdatePayload,
  HarvestTypesApi,
} from "@tornatura/coreapis";
import { getCoreApiConfiguration } from "../../../services/utils";
import { AuxState } from "../../../hooks";
import { RootState } from "../../../store";

const harvestTypesAdapter = createEntityAdapter<HarvestType, string>({
  selectId: (harvestType: HarvestType) => harvestType.id,
  sortComparer: (a, b) => {
    const sortOrderA = a.sortOrder ?? 0;
    const sortOrderB = b.sortOrder ?? 0;
    if (sortOrderA !== sortOrderB) {
      return sortOrderA - sortOrderB;
    }
    return a.label.localeCompare(b.label);
  },
});

const initialState = harvestTypesAdapter.getInitialState<AuxState>({
  status: "idle",
  total: 0,
  error: undefined,
  currentRequestId: "",
});

interface IFetchHarvestTypes {
  page?: number;
  limit?: number;
  active?: boolean;
  includeInactive?: boolean;
}

export const fetchHarvestTypes = createAsyncThunk(
  "harvestTypes/fetchHarvestTypes",
  async ({ page = 1, limit = 1000, active, includeInactive = true }: IFetchHarvestTypes = {}) => {
    const apiConfig = await getCoreApiConfiguration();
    const harvestTypesApi = new HarvestTypesApi(apiConfig);
    const response = await harvestTypesApi.listHarvestTypes(page, limit, active, includeInactive);
    return response.data;
  }
);

export const fetchHarvestType = createAsyncThunk(
  "harvestTypes/fetchHarvestType",
  async (harvestTypeId: string, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const harvestTypesApi = new HarvestTypesApi(apiConfig);
    try {
      const response = await harvestTypesApi.getHarvestType(harvestTypeId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const addHarvestType = createAsyncThunk(
  "harvestTypes/addHarvestType",
  async (body: HarvestTypeCreatePayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const harvestTypesApi = new HarvestTypesApi(apiConfig);
    try {
      const response = await harvestTypesApi.createHarvestType(body);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

interface IUpdateHarvestTypePayload {
  harvestTypeId: string;
  body: HarvestTypeUpdatePayload;
}

export const updateHarvestType = createAsyncThunk(
  "harvestTypes/updateHarvestType",
  async ({ harvestTypeId, body }: IUpdateHarvestTypePayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const harvestTypesApi = new HarvestTypesApi(apiConfig);
    try {
      const response = await harvestTypesApi.updateHarvestType(body, harvestTypeId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const deleteHarvestType = createAsyncThunk(
  "harvestTypes/deleteHarvestType",
  async (harvestTypeId: string, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const harvestTypesApi = new HarvestTypesApi(apiConfig);
    try {
      await harvestTypesApi.deleteHarvestType(harvestTypeId);
      return harvestTypeId;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

const harvestTypesSlice = createSlice({
  name: "harvestTypes",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(fetchHarvestTypes.pending, (state) => {
      state.status = "pending";
    });

    builder.addCase(fetchHarvestTypes.fulfilled, (state, action) => {
      state.status = "succeeded";
      state.total = action.payload.total;
      harvestTypesAdapter.setAll(state, action.payload.data as HarvestType[]);
    });

    builder.addCase(fetchHarvestTypes.rejected, (state, action) => {
      state.status = "failed";
      state.error = action.error.message;
    });

    builder.addCase(fetchHarvestType.fulfilled, (state, action) => {
      harvestTypesAdapter.upsertOne(state, action.payload as HarvestType);
    });

    builder.addCase(addHarvestType.fulfilled, (state, action) => {
      harvestTypesAdapter.upsertOne(state, action.payload as HarvestType);
    });

    builder.addCase(updateHarvestType.fulfilled, (state, action) => {
      harvestTypesAdapter.upsertOne(state, action.payload as HarvestType);
    });

    builder.addCase(deleteHarvestType.fulfilled, (state, action) => {
      harvestTypesAdapter.removeOne(state, action.payload as string);
    });
  },
});

const selectors = harvestTypesAdapter.getSelectors<RootState>(
  (state) => state.harvestTypes
);

export const harvestTypesSelectors = {
  selectHarvestTypes: selectors.selectAll,
  selectHarvestTypeById: selectors.selectById,
  selectActiveHarvestTypes: createSelector(
    [selectors.selectAll],
    (harvestTypes) => harvestTypes.filter((item) => item.active !== false)
  ),
  selectHarvestTypeByCode: createSelector(
    [
      selectors.selectAll,
      (_: RootState, harvestCode: string) => harvestCode,
    ],
    (harvestTypes, harvestCode) => harvestTypes.find((item) => item.code === harvestCode)
  ),
};

export const harvestTypesActions = {
  fetchHarvestTypesAction: fetchHarvestTypes,
  fetchHarvestTypeAction: fetchHarvestType,
  addHarvestTypeAction: addHarvestType,
  updateHarvestTypeAction: updateHarvestType,
  deleteHarvestTypeAction: deleteHarvestType,
};

export const harvestTypesReducer = harvestTypesSlice.reducer;
