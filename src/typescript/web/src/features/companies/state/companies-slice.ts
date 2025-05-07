
import {
  createSlice,
  createAsyncThunk,
  createEntityAdapter,
} from "@reduxjs/toolkit";
import { Organization, OrganizationCreatePayload, OrganizationsApi } from "@tornatura/coreapis";
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

export const getCompany = createAsyncThunk(
  "companies/getCompany",
  async (orgId: string) => {
    const apiConfig = await getCoreApiConfiguration();
    const organizationsApi = new OrganizationsApi(apiConfig);
    const company = organizationsApi.getOrganization(orgId).then((response) => {
      return response.data;
    });
    return company;
  }
);

export const addNewCompany = createAsyncThunk(
  "companies/addNewCompany",
  async (body: OrganizationCreatePayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const organizationsApi = new OrganizationsApi(apiConfig);
    try {
      const response = await organizationsApi.createOrganization(body);
      return response.data;
    } catch (error) {
      return rejectWithValue(error);
    }
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
    builder.addCase(getCompany.fulfilled, (state, action) => {
      state.status = "succeeded";
      companiesAdapter.upsertOne(state, action.payload as Organization);
    });
    builder.addCase(addNewCompany.fulfilled, (state, action) => {
      state.status = "succeeded";
      companiesAdapter.addOne(state, action.payload as Organization);
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
  setCompaniesAction: companiesSlice.actions.setCompanies,
  fetchCompaniesAction: fetchCompanies,
  getCompanyAction: getCompany,
  addNewCompanyAction: addNewCompany,
};


export const companiesReducer = companiesSlice.reducer;
