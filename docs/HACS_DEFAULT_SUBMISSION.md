# HACS Default submission packet

This file contains the exact upstream change and pull-request metadata needed
to submit `abderlahmanalhnedi/hass-blitzerde` to `hacs/default`.

## Upstream repository

- Repository: `hacs/default`
- Base branch: `master`
- File: `integration`
- Category: Integration

## Exact upstream change

The `integration` file is alphabetically sorted. Insert this entry between
`Aasikki/daily-fingerpori` and `abhichandra21/ha-flavoroftheday`:

```diff
   "AaronDavidSchneider/SonosAlarm",
   "aaronmayeux/ha-hurricane-tracker",
   "Aasikki/daily-fingerpori",
+  "abderlahmanalhnedi/hass-blitzerde",
   "abhichandra21/ha-flavoroftheday",
   "ablyler/home-assistant-aquahawk",
```

## Pull request title

```text
Adds new integration [abderlahmanalhnedi/hass-blitzerde]
```

## Pull request body

```markdown
## Checklist

- [x] I've read the [publishing documentation](https://hacs.xyz/docs/publish/start).
- [x] I've added the [HACS action](https://hacs.xyz/docs/publish/action) to my repository.
- [x] (For integrations only) I've added the [hassfest action](https://developers.home-assistant.io/blog/2020/04/16/hassfest/) to my repository.
- [x] The actions are passing without any disabled checks in my repository.
- [x] I've added a link to the action run on my repository below in the links section.
- [x] I've created a new release of the repository after the validation actions were run successfully.

## Links

Link to current release: https://github.com/abderlahmanalhnedi/hass-blitzerde/releases/tag/v1.4.0
Link to successful HACS action (without the `ignore` key): https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/runs/34336399056
Link to successful hassfest action (if integration): https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/runs/34336398998
```

## Verified publication evidence

- Release: `v1.4.0`
- Release asset: `blitzerde-v1.4.0.zip`
- HACS validation: success, no ignored checks
- Hassfest: success
- GitHub Issues: enabled
- Repository Topics: configured
- GitHub SPDX license detection: `MIT`
- Manifest version: `1.4.0`

## Remaining external action

The connected GitHub integration can read `hacs/default` but cannot create a
fork of another repository. A fork under the maintainer account is therefore
the only manual prerequisite left. Once
`abderlahmanalhnedi/default` exists as a fork of `hacs/default`, the
submission branch, one-line edit and upstream pull request can be created from
that fork.
