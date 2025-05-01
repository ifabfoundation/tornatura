import { RootState } from "../../../store";
import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";
import { User as UserState} from "@tornatura/coreapis";


const initialState: UserState = {
  id: "",
  firstName: "Tornatura",
  lastName: "User",
  email: "user@example.com",
  emailVerified: false,
  enabled: true,
  accountType: "Admin",
  organizations: [],
  creationTime: 1
};

const userSlice = createSlice({
  name: "user",
  initialState,
  reducers: {
    setCurrentUser(state, action: PayloadAction<UserState>) {
      state.firstName = action.payload.firstName;
      state.lastName = action.payload.lastName;
      state.email = action.payload.email;
      state.emailVerified = action.payload.emailVerified;
      state.enabled = action.payload.enabled;
      state.creationTime = action.payload.creationTime;
      state.accountType = action.payload.accountType;
      state.organizations = action.payload.organizations;
      state.id = action.payload.id;
      
    },
    resetUser(state) {
      state.firstName = initialState.firstName,
      state.lastName = initialState.lastName,
      state.email = initialState.email;
      state.emailVerified = initialState.emailVerified;
      state.enabled = initialState.enabled;
      state.creationTime = initialState.creationTime;
      state.accountType = initialState.accountType;
      state.organizations = initialState.organizations;
      state.id = initialState.id;
    },
  },
});

export const userSelectors = {
  selectUser: (state: RootState) => state.users,
};

export const userActions = {
  setCurrentUserAction: userSlice.actions.setCurrentUser,
  resetUserAction: userSlice.actions.resetUser,
};

export const userReducer = userSlice.reducer;
