import React, { useCallback, useState } from "react";
import {
  Modal,
  Button,
  Form,
  Icon,
  List,
  Label,
  Message,
} from "semantic-ui-react";
import { i18next } from "@translations/oarepo_communities";
import { useConfirmationModal, OARepoDepositSerializer } from "@js/oarepo_ui";
import {
  TextAreaField,
  http,
  ErrorLabel,
  FieldLabel,
} from "react-invenio-forms";
import { Formik } from "formik";
import PropTypes from "prop-types";
import _debounce from "lodash/debounce";
import { serializeMembers, findAndValidateEmails } from "./util";

export const CommunityInvitationsModal = ({ rolesCanInvite, community }) => {
  const { isOpen, close, open } = useConfirmationModal();
  const [successMessage, setSuccessMessage] = useState("");
  const [httpError, setHttpError] = useState("");

  const handleClose = () => {
    setSuccessMessage("");
    setHttpError("");
    close();
  }

  const onSubmit = async (values, { setSubmitting, resetForm }) => {
    const serializer = new OARepoDepositSerializer(
      ["membersEmails", "emails"],
      []
    );
    const valuesCopy = { ...values };
    valuesCopy.members = serializeMembers(valuesCopy.emails.validEmails);
    const serializedValues = serializer.serialize(valuesCopy);
    setSubmitting(true);
    try {
      const response = await http.post(
        community.links.invitations,
        serializedValues
      );
      if (response.status === 204) {
        resetForm();
        setSuccessMessage(i18next.t("Invitations sent successfully."));
        setTimeout(() => {
          if (isOpen) {
            handleClose()
          }
        }, 2500);
      }
    } catch (error) {
      if (error.response.status >= 400) {
        console.error(error.response)
        setHttpError(`
          ${i18next.t(
            "The invitations could not be sent. Please try again later."
          )}
          ${error.response.data.message}` // TODO: These needs to get translated in invenio_communities.members.config
        );
        setTimeout(() => {
          setHttpError("")
        }, 5000);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const debouncedValidateEmails = useCallback(
    _debounce((value, setFieldValue) => {
      const emails = findAndValidateEmails(value);
      setFieldValue("emails", emails);
    }, 1000),
    []
  );

  const handleChange = (value, setFieldValue) => {
    setFieldValue("membersEmails", value);
    debouncedValidateEmails(value, setFieldValue);
  };
  const usersCanInvite = rolesCanInvite.user;
  return (
    <Formik
      onSubmit={onSubmit}
      initialValues={{
        membersEmails: "",
        members: [],
        role: "member",
        emails: { validEmails: [], invalidEmails: [] },
      }}
      validateOnChange={false}
      validateOnBlur={true}
      enableReinitialize={true}
    >
      {({ values, setFieldValue, handleSubmit, resetForm, isSubmitting }) => {
        const validEmailsCount = values.emails.validEmails.length;
        const invalidEmailsCount = values.emails.invalidEmails.length;
        return (
          <Modal
            className="form-modal community-invitations"
            closeIcon
            open={isOpen}
            onClose={handleClose}
            onOpen={open}
            trigger={
              <Button
                className="fluid-responsive"
                content={i18next.t("Invite...")}
                positive
                fluid
                compact
                icon="user plus"
                labelPosition="left"
                aria-expanded={isOpen}
                aria-haspopup="dialog"
              />
            }
          >
            <Modal.Header>
              {i18next.t("Invite users to the {{communityTitle}} community", {
                communityTitle: community.metadata.title,
              })}
            </Modal.Header>
            <Modal.Content>
              <Form>
                <Form.Field>
                  <TextAreaField
                    fieldPath="membersEmails"
                    required
                    autoFocus
                    label={
                      <FieldLabel
                        label={
                          <label htmlFor="membersEmails">
                            {validEmailsCount > 0 &&
                            invalidEmailsCount === 0 ? (
                              <Icon name="check circle" color="green" />
                            ) : null}
                            {i18next.t("Members")}
                          </label>
                        }
                      />
                    }
                    onChange={(e, { value }) =>
                      handleChange(value, setFieldValue)
                    }
                  />
                  {invalidEmailsCount > 0 && (
                    <Label
                      className="mt-0"
                      pointing
                      prompt
                      content={`${i18next.t(
                        "Invalid emails"
                      )}: ${values.emails.invalidEmails.join(", ")}`}
                    />
                  )}
                  <label className="helptext">
                    {i18next.t(
                      `Emails shall be provided on separate lines. 
                    Acceptable formats are johndoe@user.com or Doe John <johndoe@user.com>. 
                    Note that invitations shall be sent only to the valid email addresses.`
                    )}
                  </label>
                </Form.Field>
                <Form.Field required className="rel-mt-1">
                  <FieldLabel label={i18next.t("Role")} />
                  <List selection>
                    {usersCanInvite.map((u) => (
                      <List.Item
                        key={u.name}
                        onClick={() => {
                          if (values.role === u.name) return;
                          setFieldValue("role", u.name);
                        }}
                        active={values.role === u.name}
                      >
                        <List.Content>
                          <List.Header>{u.title}</List.Header>
                          <List.Description>{u.description}</List.Description>
                        </List.Content>
                      </List.Item>
                    ))}
                  </List>
                  <ErrorLabel fieldPath="role" />
                </Form.Field>
              </Form>
              {successMessage && <Message positive>{successMessage}</Message>}
              {httpError && <Message negative>{httpError}</Message>}
            </Modal.Content>
            <Modal.Actions>
              <Button
                onClick={() => {
                  close();
                  resetForm();
                }}
                floated="left"
              >
                <Icon name="remove" /> {i18next.t("Cancel")}
              </Button>
              <Button
                primary
                onClick={handleSubmit}
                disabled={validEmailsCount === 0 || isSubmitting}
                loading={isSubmitting}
              >
                <Icon name="checkmark" /> {i18next.t("Invite")}{" "}
                {validEmailsCount > 0 && `(${validEmailsCount})`}
              </Button>
            </Modal.Actions>
          </Modal>
        );
      }}
    </Formik>
  );
};

CommunityInvitationsModal.propTypes = {
  rolesCanInvite: PropTypes.object.isRequired,
  community: PropTypes.object.isRequired,
};
