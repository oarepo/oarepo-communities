import React from "react";
import { parametrize } from "react-overridable";
import { i18next } from "@translations/oarepo_communities";
import {
  createSearchAppsInit,
  parseSearchAppConfigs,
  SearchappSearchbarElement,
  DynamicResultsListItem,
  SearchAppLayoutWithSearchbarHOC,
  SearchAppResultViewWithSearchbar,
} from "@js/oarepo_ui";

const [{ overridableIdPrefix }] = parseSearchAppConfigs();

const SearchAppResultViewWithSearchbarWAppName = parametrize(
  SearchAppResultViewWithSearchbar,
  {
    appName: overridableIdPrefix,
  }
);

export const DashboardUploadsSearchLayout = SearchAppLayoutWithSearchbarHOC({
  placeholder: i18next.t("Search inside the community..."),

  appName: overridableIdPrefix,
});
export const componentOverrides = {
  [`${overridableIdPrefix}.ResultsList.item`]: DynamicResultsListItem,
  [`${overridableIdPrefix}.SearchBar.element`]: SearchappSearchbarElement,
  [`${overridableIdPrefix}.SearchApp.results`]:
    SearchAppResultViewWithSearchbarWAppName,
  [`${overridableIdPrefix}.SearchApp.layout`]: DashboardUploadsSearchLayout,
};

createSearchAppsInit({ componentOverrides });
