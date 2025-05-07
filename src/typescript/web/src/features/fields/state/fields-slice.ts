
import {
  createSlice,
  createAsyncThunk,
  createEntityAdapter,
  createSelector,
} from "@reduxjs/toolkit";
import { AgriField, AgriFieldsApi } from "@tornatura/coreapis";
import { getCoreApiConfiguration } from "../../../services/utils";
import { AuxState } from "../../../hooks";
import { RootState } from "../../../store";


const fieldsAdapter = createEntityAdapter<AgriField, string>({
  selectId: (field: AgriField) => field.id,
});

const initialState = fieldsAdapter.getInitialState<AuxState>({
  status: "idle",
  total: 0,
  error: undefined,
  currentRequestId: "",
});

export const fetchCompanyFields = createAsyncThunk(
  "fields/fetchCompanyFields",
  async (orgId: string, ) => {
    const apiConfig = await getCoreApiConfiguration();
    const agrifieldsApi = new AgriFieldsApi(apiConfig);
    const data = agrifieldsApi.listAgrifields(orgId).then((response) => {
      return response.data;
    });
    return data;
  }
);

const fieldsSlice = createSlice({
  name: "fields",
  initialState,
  reducers: {
  },
  extraReducers: (builder) => {
    builder.addCase(fetchCompanyFields.pending, (state) => {
      state.status = "pending";
    });

    builder.addCase(fetchCompanyFields.fulfilled, (state, action) => {
      state.status = "succeeded";
      state.total = action.payload.total;
      fieldsAdapter.upsertMany(state, action.payload.data as AgriField[]);
    });

    builder.addCase(fetchCompanyFields.rejected, (state, action) => {
      state.status = "failed";
      state.error = action.error.message;
    });
  },
});

const selectors = fieldsAdapter.getSelectors<RootState>(
  (state) => state.fields
);

export const fieldsSelectors = {
  selectFieldbyId: selectors.selectById,
  selectFieldsByOrgId: createSelector(
    [
      selectors.selectAll,
      (state, orgId) => orgId
    ],
    (fields, orgId) => fields.filter((item: AgriField) => item.orgId === orgId)
  )
};

export const fieldsActions = {
  fetchCompanyFieldsAction: fetchCompanyFields,
};


export const fieldsReducer = fieldsSlice.reducer;
