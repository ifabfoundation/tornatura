
import {
  createSlice,
  createAsyncThunk,
  createEntityAdapter,
  createSelector,
} from "@reduxjs/toolkit";
import { AgriField, AgriFieldMutationPayload, AgriFieldsApi } from "@tornatura/coreapis";
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

interface AddNewFieldPayload {
  orgId: string;
  body: AgriFieldMutationPayload;
}

export const addNewField = createAsyncThunk(
  "fields/addNewField",
  async ({orgId, body}: AddNewFieldPayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration()
    const apiInstance = new AgriFieldsApi(apiConfig);
    try {
      const response = await apiInstance.createAgrifield(body, orgId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
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

    builder.addCase(addNewField.fulfilled, (state, action) => {
      fieldsAdapter.upsertOne(state, action.payload as AgriField);
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
      (_, orgId) => orgId
    ],
    (fields, orgId) => fields.filter((item: AgriField) => item.orgId === orgId)
  )
};

export const fieldsActions = {
  fetchCompanyFieldsAction: fetchCompanyFields,
  addNewFieldAction: addNewField,
};


export const fieldsReducer = fieldsSlice.reducer;
