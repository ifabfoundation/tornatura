
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

interface UpdateFieldPayload {
  orgId: string;
  fieldId: string;
  body: AgriFieldMutationPayload;
}

export const updateField = createAsyncThunk(
  "fields/updateField",
  async ({orgId, fieldId, body}: UpdateFieldPayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration()
    const apiInstance = new AgriFieldsApi(apiConfig);
    try {
      const response = await apiInstance.updateAgrifield(body, orgId, fieldId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
  }
);

interface deleteFieldPayload {
  orgId: string;
  fieldId: string;
}

export const deleteField = createAsyncThunk(
  "fields/deleteField",
  async ({orgId, fieldId}: deleteFieldPayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration()
    const apiInstance = new AgriFieldsApi(apiConfig);
    try {
      await apiInstance.deleteAgrifield(orgId, fieldId);
      return fieldId;
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

    builder.addCase(updateField.fulfilled, (state, action) => {
      fieldsAdapter.upsertOne(state, action.payload as AgriField);
    });

    builder.addCase(deleteField.fulfilled, (state, action) => {
      fieldsAdapter.removeOne(state, action.payload);
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
  updateFieldAction: updateField,
  deleteFieldAction: deleteField,
};


export const fieldsReducer = fieldsSlice.reducer;
