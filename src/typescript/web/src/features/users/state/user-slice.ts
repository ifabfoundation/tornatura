import { RootState } from "../../../store";
import { createAsyncThunk, createEntityAdapter, createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";
import { AccountTypeEnum, UsersApi, User as UserState, UserUpdatePayload } from "@tornatura/coreapis";
import { getCoreApiConfiguration } from "../../../services/utils";
import { fallbacks } from "../../../assets/images/fallback";

interface AuxState {
  currentUser: UserState;
}

const usersAdapter = createEntityAdapter<UserState, string>({
  selectId: (user: UserState) => user.id || "default",
});

const initialState = usersAdapter.getInitialState<AuxState>({
  currentUser: {
    id: "",
    firstName: "Tornatura",
    lastName: "User",
    email: "user@example.com",
    piva: "",
    emailVerified: false,
    enabled: true,
    accountType: AccountTypeEnum.Admin,
    phone: "",
    organizations: [],
    creationTime: 1,
    avatar: fallbacks.avatar,
  },
});

export const fetchUsers = createAsyncThunk("users/fetchUsers", async () => {
  const apiConfig = await getCoreApiConfiguration();
  const usersApi = new UsersApi(apiConfig);
  const users = usersApi.listUsers().then((response) => {
    return response.data;
  });
  return users;
});

export const updateUser = createAsyncThunk("users/updateUser", async (body: UserUpdatePayload) => {
  const apiConfig = await getCoreApiConfiguration();
  const usersApi = new UsersApi(apiConfig);
  const response = await usersApi.updateUser(body);
  return response.data;
});


const usersSlice = createSlice({
  name: "users",
  initialState,
  reducers: {
    setCurrentUser(state, action: PayloadAction<UserState>) {
      state.currentUser.firstName = action.payload.firstName;
      state.currentUser.lastName = action.payload.lastName;
      state.currentUser.email = action.payload.email;
      state.currentUser.emailVerified = action.payload.emailVerified;
      state.currentUser.enabled = action.payload.enabled;
      state.currentUser.creationTime = action.payload.creationTime;
      state.currentUser.accountType = action.payload.accountType;
      state.currentUser.phone = action.payload.phone;
      state.currentUser.piva = action.payload.piva;
      state.currentUser.organizations = action.payload.organizations;
      state.currentUser.id = action.payload.id;
      state.currentUser.avatar = action.payload.avatar ? action.payload.avatar : fallbacks.avatar;
    },
    resetCurrentUser(state) {
      state.currentUser.firstName = initialState.currentUser.firstName;
      state.currentUser.lastName = initialState.currentUser.lastName;
      state.currentUser.email = initialState.currentUser.email;
      state.currentUser.emailVerified = initialState.currentUser.emailVerified;
      state.currentUser.enabled = initialState.currentUser.enabled;
      state.currentUser.creationTime = initialState.currentUser.creationTime;
      state.currentUser.accountType = initialState.currentUser.accountType;
      state.currentUser.organizations = initialState.currentUser.organizations;
      state.currentUser.phone = initialState.currentUser.phone;
      state.currentUser.id = initialState.currentUser.id;
      state.currentUser.avatar = initialState.currentUser.avatar;
      state.currentUser.piva = initialState.currentUser.piva;
    },
  },
  extraReducers: (builder) => {
    builder.addCase(fetchUsers.fulfilled, (state, action) => {
      usersAdapter.upsertMany(state, action.payload.data as UserState[]);
    });
    builder.addCase(updateUser.fulfilled, (state, action) => {
      usersAdapter.upsertOne(state, action.payload as UserState);
      if (state.currentUser.id === action.payload.id) {
        state.currentUser = action.payload;
        state.currentUser.avatar = action.payload.avatar ? action.payload.avatar : fallbacks.avatar;
      }
    });
  },
});

const selectors = usersAdapter.getSelectors<RootState>((state) => state.users);

export const userSelectors = {
  selectAllUsers: selectors.selectAll,
  selectUsersById: selectors.selectById,
  selectCurrentUser: (state: RootState) => state.users.currentUser,
};

export const userActions = {
  fetchUsersAction: fetchUsers,
  setCurrentUserAction: usersSlice.actions.setCurrentUser,
  resetCurrentUserAction: usersSlice.actions.resetCurrentUser,
  updateUserAction: updateUser,
};

export const usersReducer = usersSlice.reducer;
