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

Link to current release: https://github.com/abderlahmanalhnedi/hass-blitzerde/releases/tag/v1.4.3
Link to successful HACS action (without the `ignore` key): https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/runs/34339861502
Link to successful hassfest action (if integration): https://github.com/abderlahmanalhnedi/hass-blitzerde/actions/runs/34339861714
```

## Verified publication evidence

- Release: `v1.4.3`
- Release commit: `9874a91ba8782c885911b20ccfc079684ffcd27d`
- Release asset: `blitzerde-v1.4.3.zip`
- HACS validation: success, no ignored checks
- Hassfest: success
- Home Assistant tests: success
- Code quality: success
- CodeQL: success
- GitHub Issues: enabled
- Repository Topics: configured
- GitHub SPDX license detection: `MIT`
- Manifest version: `1.4.3`

## Final pre-submission verification

Before opening the upstream pull request:

1. Verify a clean HACS install of `v1.4.3` on a real Home Assistant instance.
2. Restart Home Assistant and complete the Blitzer.de config flow.
3. Confirm the integration loads, creates entities and receives report data.
4. Verify HACS can update/reinstall the release without a custom local copy.
5. Re-check that HACS Action and Hassfest are still green.

## Remaining external action

As of 2026-09-09, the maintainer fork `abderlahmanalhnedi/default` does not
exist. The connected GitHub integration can read `hacs/default`, but it
cannot create a fork of another repository.

Create `abderlahmanalhnedi/default` as a fork of `hacs/default`. Once that
fork exists, create a submission branch in the fork, add the one-line entry
shown above, and open the pull request against `hacs/default:master`.

No upstream pull request should be opened until the real HACS clean-install
verification has been completed.
