import { configureStore } from "@reduxjs/toolkit";
import { userReducer } from "./features/users/state/user-slice";
import { headerbarReducer } from "./features/headerbar/state/headerbar-slice";
import { companiesReducer } from "./features/companies/state/companies-slice";

const store = configureStore({
  reducer: {
    companies: companiesReducer,
    headerbar: headerbarReducer,
    users: userReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;
