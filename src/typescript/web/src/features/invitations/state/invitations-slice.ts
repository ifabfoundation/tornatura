import { createSlice, createAsyncThunk, createEntityAdapter, createSelector } from "@reduxjs/toolkit";
import {
  Invitation,
  InvitationCreatePayload,
  InvitationAcceptPayload,
  InvitationValidateResponse,
  InvitationsApi,
  Configuration
} from "@tornatura/coreapis";
import { getCoreApiConfiguration } from "../../../services/utils";
import { RootState } from "../../../store";


const COREAPIS_BASE_PATH = process.env.REACT_APP_COREAPIS_SERVER_URL;

// Define adapter with primary key
const invitationsAdapter = createEntityAdapter<Invitation, string>({
  selectId: (invitation: Invitation) => invitation.id,
});

// Initial state with AuxState interface for status tracking
interface AuxState {
  status: "idle" | "pending" | "succeeded" | "failed";
  error: any;
  currentRequestId: string;
  // Track validation state separately
  validationStatus: "idle" | "pending" | "succeeded" | "failed";
  validatedInvitation: InvitationValidateResponse | null;
}

const initialState = invitationsAdapter.getInitialState<AuxState>({
  status: "idle",
  error: undefined,
  currentRequestId: "",
  validationStatus: "idle",
  validatedInvitation: null,
});

// Create async thunks for API calls

/**
 * Fetch all invitations for an organization
 */
export const fetchOrganizationInvitations = createAsyncThunk(
  "invitations/fetchOrganizationInvitations",
  async ({ orgId, status }: { orgId: string; status?: string }) => {
    const apiConfig = await getCoreApiConfiguration();
    const invitationsApi = new InvitationsApi(apiConfig);
    // API method now uses query parameters: /invitations/byOrg?org_id=...&status=...
    return invitationsApi.listOrganizationInvitations(orgId, status).then((response) => response.data);
  }
);

/**
 * Fetch invitations for current user
 */
export const fetchMyInvitations = createAsyncThunk(
  "invitations/fetchMyInvitations",
  async () => {
    const apiConfig = await getCoreApiConfiguration();
    const invitationsApi = new InvitationsApi(apiConfig);
    return invitationsApi.listMyInvitations().then((response) => response.data);
  }
);

/**
 * Create a new invitation
 * The orgId is taken from the payload - can be omitted/null for agronomist inviting non-existent company owner
 */
export const sendInvitation = createAsyncThunk(
  "invitations/sendInvitation",
  async (body: InvitationCreatePayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const invitationsApi = new InvitationsApi(apiConfig);
    try {
      // Clean payload: remove undefined values to ensure proper JSON serialization
      const cleanPayload = {
        email: body.email,
        role: body.role,
        ...(body.orgId !== undefined && { orgId: body.orgId })
      };
      const response = await invitationsApi.createInvitation(cleanPayload as InvitationCreatePayload);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

/**
 * Validate invitation token (public, no auth)
 */
export const validateInvitationToken = createAsyncThunk(
  "invitations/validateToken",
  async (token: string, { rejectWithValue }) => {
    const apiConfig = new Configuration({
      basePath: `${COREAPIS_BASE_PATH}`,
    });
    const invitationsApi = new InvitationsApi(apiConfig);
    try {
      const response = await invitationsApi.validateInvitationToken(token);
      return response.data;
    } catch (error: any) {
      console.log(error);
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

/**
 * Accept an invitation
 */
export const acceptInvitation = createAsyncThunk(
  "invitations/acceptInvitation",
  async (body: InvitationAcceptPayload, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const invitationsApi = new InvitationsApi(apiConfig);
    try {
      const response = await invitationsApi.acceptInvitation(body);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

/**
 * Decline an invitation
 */
export const declineInvitation = createAsyncThunk(
  "invitations/declineInvitation",
  async (token: string, { rejectWithValue }) => {
    const apiConfig = new Configuration({
      basePath: `${COREAPIS_BASE_PATH}`,
    });
    const invitationsApi = new InvitationsApi(apiConfig);
    try {
      const response = await invitationsApi.declineInvitation({ token });
      return { token, response: response.data };
    } catch (error: any) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

/**
 * Cancel (revoke) a sent invitation
 */
export const cancelInvitation = createAsyncThunk(
  "invitations/cancelInvitation",
  async (invitationId: string, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const invitationsApi = new InvitationsApi(apiConfig);
    try {
      const response = await invitationsApi.revokeInvitation(invitationId);
      return { invitationId, response: response.data };
    } catch (error: any) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

/**
 * Resend an invitation
 */
export const resendInvitation = createAsyncThunk(
  "invitations/resendInvitation",
  async (invitationId: string, { rejectWithValue }) => {
    const apiConfig = await getCoreApiConfiguration();
    const invitationsApi = new InvitationsApi(apiConfig);
    try {
      const response = await invitationsApi.resendInvitation(invitationId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

// Create slice with reducers and extraReducers
const invitationsSlice = createSlice({
  name: "invitations",
  initialState,
  reducers: {
    // Clear validation state
    clearValidation: (state) => {
      state.validationStatus = "idle";
      state.validatedInvitation = null;
    },
    // Clear error
    clearError: (state) => {
      state.error = undefined;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch organization invitations
      .addCase(fetchOrganizationInvitations.pending, (state) => {
        state.status = "pending";
      })
      .addCase(fetchOrganizationInvitations.fulfilled, (state, action) => {
        state.status = "succeeded";
        invitationsAdapter.setAll(state, action.payload);
      })
      .addCase(fetchOrganizationInvitations.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      // Fetch my invitations
      .addCase(fetchMyInvitations.pending, (state) => {
        state.status = "pending";
      })
      .addCase(fetchMyInvitations.fulfilled, (state, action) => {
        state.status = "succeeded";
        invitationsAdapter.setAll(state, action.payload);
      })
      .addCase(fetchMyInvitations.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      // Send invitation
      .addCase(sendInvitation.pending, (state) => {
        state.status = "pending";
      })
      .addCase(sendInvitation.fulfilled, (state, action) => {
        state.status = "succeeded";
        invitationsAdapter.addOne(state, action.payload);
      })
      .addCase(sendInvitation.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload;
      })
      // Validate token
      .addCase(validateInvitationToken.pending, (state) => {
        state.validationStatus = "pending";
      })
      .addCase(validateInvitationToken.fulfilled, (state, action) => {
        state.validationStatus = "succeeded";
        state.validatedInvitation = action.payload;
      })
      .addCase(validateInvitationToken.rejected, (state, action) => {
        state.validationStatus = "failed";
        state.error = action.payload;
      })
      // Accept invitation
      .addCase(acceptInvitation.pending, (state) => {
        state.status = "pending";
      })
      .addCase(acceptInvitation.fulfilled, (state) => {
        state.status = "succeeded";
        // Clear validated invitation after acceptance
        state.validatedInvitation = null;
      })
      .addCase(acceptInvitation.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload;
      })
      // Decline invitation
      .addCase(declineInvitation.fulfilled, (state) => {
        state.status = "succeeded";
        state.validatedInvitation = null;
      })
      .addCase(declineInvitation.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload;
      })
      // Cancel invitation
      .addCase(cancelInvitation.fulfilled, (state, action) => {
        state.status = "succeeded";
        invitationsAdapter.removeOne(state, action.payload.invitationId);
      })
      .addCase(cancelInvitation.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload;
      })
      // Resend invitation
      .addCase(resendInvitation.pending, (state) => {
        state.status = "pending";
      })
      .addCase(resendInvitation.fulfilled, (state) => {
        state.status = "succeeded";
      })
      .addCase(resendInvitation.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload;
      });
  },
});

// Selectors
const selectors = invitationsAdapter.getSelectors<RootState>(
  (state) => state.invitations
);

export const invitationsSelectors = {
  selectAllInvitations: selectors.selectAll,
  selectInvitationById: selectors.selectById,
  selectInvitationsByOrgId: createSelector(
    [
      selectors.selectAll,
      (_: RootState, orgId?: string) => orgId,
    ],
    (invitations, orgId) =>
      orgId ? invitations.filter((invitation) => invitation.orgId === orgId) : []
  ),
  selectMyInvitations: createSelector(
    [
      selectors.selectAll,
      (state: RootState) => state.users.currentUser.email,
    ],
    (invitations, currentUserEmail) =>
      invitations.filter((invitation) => invitation.email === currentUserEmail)
  ),
  selectInvitationsStatus: (state: RootState) => state.invitations.status,
  selectInvitationsError: (state: RootState) => state.invitations.error,
  selectValidationStatus: (state: RootState) => state.invitations.validationStatus,
  selectValidatedInvitation: (state: RootState) => state.invitations.validatedInvitation,
};

// Actions
export const invitationsActions = {
  fetchOrganizationInvitationsAction: fetchOrganizationInvitations,
  fetchMyInvitationsAction: fetchMyInvitations,
  sendInvitationAction: sendInvitation,
  validateInvitationTokenAction: validateInvitationToken,
  acceptInvitationAction: acceptInvitation,
  declineInvitationAction: declineInvitation,
  cancelInvitationAction: cancelInvitation,
  resendInvitationAction: resendInvitation,
  clearValidation: invitationsSlice.actions.clearValidation,
  clearError: invitationsSlice.actions.clearError,
};

export const invitationsReducer = invitationsSlice.reducer;
