import PropTypes from "prop-types";
import { i18next } from "@translations/oarepo_communities";
import { CommunityItem } from "@js/communities_components/CommunitySelector/CommunityItem";
import { useFormikContext, getIn } from "formik";
import React from "react";
import { OverridableContext, overrideStore } from "react-overridable";
import {
  EmptyResults,
  Error,
  InvenioSearchApi,
  ReactSearchKit,
  ResultsLoader,
  SearchBar,
  Pagination,
  withState,
} from "react-searchkit";
import { Grid, Message, List } from "semantic-ui-react";
import { EmptyResultsElement } from "@js/oarepo_ui";

const appName = "OarepoCommunities.SecondaryCommunitySelector";
const overriddenComponents = {
  [`${appName}.EmptyResults.element`]: EmptyResultsElement,
  ...overrideStore.getAll(),
};

const searchConfig = {
  searchApi: {
    axios: {
      headers: {
        Accept: "application/vnd.inveniordm.v1+json",
      },
      url: "/api/user/communities",
    },
  },
  initialQueryState: {
    size: 5,
    page: 1,
    sortBy: "newest",
  },
};

const SecondaryCommunitySelector = ({ fieldPath }) => {
  const { values, errors, setFieldValue, setFieldError } = useFormikContext();
  const selectedCommunityId = getIn(values, fieldPath, "");

  const searchApi = new InvenioSearchApi(searchConfig.searchApi);

  const handleClick = (communityId) => {
    if (selectedCommunityId === communityId) return;
    setFieldValue(fieldPath, communityId);
    setFieldError(fieldPath, null);
  };

  return (
    <OverridableContext.Provider value={overriddenComponents}>
      <ReactSearchKit
        searchApi={searchApi}
        urlHandlerApi={{ enabled: false }}
        initialQueryState={searchConfig.initialQueryState}
        appName="OarepoCommunities.SecondaryCommunitySelector"
      >
        <Grid>
          <Grid.Row>
            <Grid.Column width={8} floated="left" verticalAlign="middle">
              <SearchBar
                placeholder={i18next.t("Search in my communities...")}
                autofocus
                actionProps={{
                  icon: "search",
                  content: null,
                  className: "search",
                }}
              />
            </Grid.Column>
          </Grid.Row>
          {getIn(errors, fieldPath, null) && (
            <Grid.Row>
              <Grid.Column width={16}>
                <Message negative>
                  <Message.Content>{getIn(errors, fieldPath)}</Message.Content>
                </Message>
              </Grid.Column>
            </Grid.Row>
          )}
          <Grid.Row verticalAlign="middle">
            <Grid.Column>
              <ResultsLoader>
                <EmptyResults />
                <Error />
                <CommunityResults
                  handleClick={handleClick}
                  selectedCommunityId={selectedCommunityId}
                />
                <div className="centered">
                  <Pagination
                    options={{
                      size: "mini",
                      showFirst: false,
                      showLast: false,
                    }}
                    showWhenOnlyOnePage={false}
                  />
                </div>
              </ResultsLoader>
            </Grid.Column>
          </Grid.Row>
        </Grid>
      </ReactSearchKit>
    </OverridableContext.Provider>
  );
};

export default SecondaryCommunitySelector;

SecondaryCommunitySelector.propTypes = {
  fieldPath: PropTypes.string.isRequired,
};

export const CommunityResults = withState(
  ({ currentResultsState: results, handleClick, selectedCommunityId }) => {
    return (
      <List selection>
        {results.data.hits.map((result) => {
          const active = selectedCommunityId === result.id;
          return (
            <CommunityItem
              renderLinks={false}
              key={result.id}
              active={active}
              handleClick={handleClick}
              community={{
                id: result.id,
                title: result.metadata?.title,
                website: result.metadata?.website,
                logo: result.links?.logo,
                organizations: result.metadata?.organizations,
                links: result.links,
              }}
            />
          );
        })}
      </List>
    );
  }
);

CommunityResults.propTypes = {
  currentResultsState: PropTypes.object,
  handleClick: PropTypes.func.isRequired,
  selectedCommunityId: PropTypes.string.isRequired,
};
