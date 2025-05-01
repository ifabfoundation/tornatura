
import {
  createSlice,
  createAsyncThunk,
  createEntityAdapter,
} from "@reduxjs/toolkit";
import { Organization, OrganizationsApi } from "@tornatura/coreapis";
import { getCoreApiConfiguration } from "../../../services/utils";
import { AuxState } from "../../../hooks";
import { RootState } from "../../../store";


const companiesAdapter = createEntityAdapter<Organization, string>({
  selectId: (organization: Organization) => organization.orgId || "default",
});

const initialState = companiesAdapter.getInitialState<AuxState>({
  status: "idle",
  total: 0,
  error: undefined,
  currentRequestId: "",
});

export const fetchCompanies = createAsyncThunk(
  "companies/fetchCompanies",
  async () => {
    const apiConfig = await getCoreApiConfiguration();
    const organizationsApi = new OrganizationsApi(apiConfig);
    const companies = organizationsApi.listOrganization().then((response) => {
      return response.data;
    });
    return companies;
  }
);

const companiesSlice = createSlice({
  name: "companies",
  initialState,
  reducers: {
    setCompanies(state, action) {
      companiesAdapter.upsertMany(state, action.payload.data as Organization[]);
    },
  },
  extraReducers: (builder) => {
    builder.addCase(fetchCompanies.pending, (state) => {
      state.status = "pending";
    });

    builder.addCase(fetchCompanies.fulfilled, (state, action) => {
      state.status = "succeeded";
      state.total = action.payload.total;
      companiesAdapter.upsertMany(state, action.payload.data as Organization[]);
    });

    builder.addCase(fetchCompanies.rejected, (state, action) => {
      state.status = "failed";
      state.error = action.error.message;
    });
  },
});

const selectors = companiesAdapter.getSelectors<RootState>(
  (state) => state.companies
);

export const companiesSelectors = {
  selectAllCompanies: selectors.selectAll,
  selectCompanybyId: selectors.selectById,
};

export const companiesActions = {
  setCompanies: companiesSlice.actions.setCompanies,
  fetchCompanies: fetchCompanies,
};


export const companiesReducer = companiesSlice.reducer;
