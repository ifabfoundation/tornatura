import {
  createSlice,
  createAsyncThunk,
  createEntityAdapter,
  createSelector,
} from "@reduxjs/toolkit";
import {
  DetectionText,
  DetectionTextCreatePayload,
  DetectionTextUpdatePayload,
  DetectionTextsApi,
} from "@tornatura/coreapis";
import { getCoreApiConfiguration } from "../../../services/utils";
import { AuxState } from "../../../hooks";
import { RootState } from "../../../store";


const detectionTextsAdapter = createEntityAdapter<DetectionText, string>({
  selectId: (detectionText: DetectionText) => detectionText.id,
});

const initialState = detectionTextsAdapter.getInitialState<AuxState>({
  status: "idle",
  total: 0,
  error: undefined,
  currentRequestId: "",
});

interface IFetchDetectionTexts {
  page?: number;
  limit?: number;
}

export const fetchDetectionTexts = createAsyncThunk(
  "detectionTexts/fetchDetectionTexts",
  async ({ page = 1, limit = 1000 }: IFetchDetectionTexts) => {
    const apiConfig = await getCoreApiConfiguration();
    const detectionTextsApi = new DetectionTextsApi(apiConfig);
    const data = detectionTextsApi
      .listDetectionTexts(page, limit)
      .then((response) => response.data);
    return data;
  }
);

export const addDetectionText = createAsyncThunk(
  "detectionTexts/addDetectionText",
  async (body: DetectionTextCreatePayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const detectionTextsApi = new DetectionTextsApi(apiConfig);
    try {
      const response = await detectionTextsApi.createDetectionText(body);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

interface IUpdateDetectionTextPayload {
  detectionTextId: string;
  body: DetectionTextUpdatePayload;
}

export const updateDetectionText = createAsyncThunk(
  "detectionTexts/updateDetectionText",
  async ({ detectionTextId, body }: IUpdateDetectionTextPayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const detectionTextsApi = new DetectionTextsApi(apiConfig);
    try {
      const response = await detectionTextsApi.updateDetectionText(body, detectionTextId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

export const deleteDetectionText = createAsyncThunk(
  "detectionTexts/deleteDetectionText",
  async (detectionTextId: string, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const detectionTextsApi = new DetectionTextsApi(apiConfig);
    try {
      await detectionTextsApi.deleteDetectionText(detectionTextId);
      return detectionTextId;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

const detectionTextsSlice = createSlice({
  name: "detectionTexts",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(fetchDetectionTexts.pending, (state) => {
      state.status = "pending";
    });

    builder.addCase(fetchDetectionTexts.fulfilled, (state, action) => {
      state.status = "succeeded";
      state.total = action.payload.total;
      detectionTextsAdapter.setAll(state, action.payload.data as DetectionText[]);
    });

    builder.addCase(fetchDetectionTexts.rejected, (state, action) => {
      state.status = "failed";
      state.error = action.error.message;
    });

    builder.addCase(addDetectionText.fulfilled, (state, action) => {
      detectionTextsAdapter.upsertOne(state, action.payload as DetectionText);
    });

    builder.addCase(updateDetectionText.fulfilled, (state, action) => {
      detectionTextsAdapter.upsertOne(state, action.payload as DetectionText);
    });

    builder.addCase(deleteDetectionText.fulfilled, (state, action) => {
      detectionTextsAdapter.removeOne(state, action.payload as string);
    });
  },
});

const selectors = detectionTextsAdapter.getSelectors<RootState>(
  (state) => state.detectionTexts
);

export const detectionTextsSelectors = {
  selectDetectionTexts: selectors.selectAll,
  selectDetectionTextById: selectors.selectById,
  selectDetectionTextsByTypologyAndMethod: createSelector(
    [
      selectors.selectAll,
      (_: RootState, typology: string) => typology,
      (_: RootState, _typology: string, method: string) => method,
    ],
    (texts, typology, method) =>
      texts.filter((item) => item.typology === typology && item.method === method)
  ),
};

export const detectionTextsActions = {
  fetchDetectionTextsAction: fetchDetectionTexts,
  addDetectionTextAction: addDetectionText,
  updateDetectionTextAction: updateDetectionText,
  deleteDetectionTextAction: deleteDetectionText,
};

export const detectionTextsReducer = detectionTextsSlice.reducer;
