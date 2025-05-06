
import {
  createSlice,
  createAsyncThunk,
  createEntityAdapter,
} from "@reduxjs/toolkit";
import { Feedback, FeedbacksApi } from "@tornatura/coreapis";
import { getCoreApiConfiguration } from "../../../services/utils";
import { AuxState } from "../../../hooks";
import { RootState } from "../../../store";


const feedbackAdapter = createEntityAdapter<Feedback, string>({
  selectId: (feedback: Feedback) => feedback.id || "default",
});

const initialState = feedbackAdapter.getInitialState<AuxState>({
  status: "idle",
  total: 0,
  error: undefined,
  currentRequestId: "",
});

export const fetchFeedback = createAsyncThunk(
  "feedback/fetchFeedback",
  async () => {
    const apiConfig = await getCoreApiConfiguration();
    const feedbacksApi = new FeedbacksApi(apiConfig);
    const feedbacks = feedbacksApi.listFeebacks().then((response) => {
      return response.data;
    });
    return feedbacks;
  }
);

const feedbackSlice = createSlice({
  name: "feedbacks",
  initialState,
  reducers: {
  },
  extraReducers: (builder) => {
    builder.addCase(fetchFeedback.pending, (state) => {
      state.status = "pending";
    });

    builder.addCase(fetchFeedback.fulfilled, (state, action) => {
      state.status = "succeeded";
      state.total = action.payload.total;
      feedbackAdapter.upsertMany(state, action.payload.data as Feedback[]);
    });

    builder.addCase(fetchFeedback.rejected, (state, action) => {
      state.status = "failed";
      state.error = action.error.message;
    });
  },
});

const selectors = feedbackAdapter.getSelectors<RootState>(
  (state) => state.feedbacks
);

export const feedbacksSelectors = {
  selectAllFeedbacks: selectors.selectAll,
  selectFeedbackById: selectors.selectById,
};

export const feedbacksActions = {
  fetchFeedbackAction: fetchFeedback,
};


export const feedbackReducer = feedbackSlice.reducer;
